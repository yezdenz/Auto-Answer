"""
Auto Answer - Main CLI entry point.
Run directly from PowerShell or Command Prompt.
"""

from __future__ import annotations
import sys
import time
import argparse
from pathlib import Path
from PIL import Image

# Ensure src is in python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from auto_answer.config import AppConfig
from auto_answer.capture.screen import capture_screen_region
from auto_answer.capture.snipper import launch_snipping_tool
from auto_answer.capture.window_detector import find_emulator_window, find_windows_by_title
from auto_answer.ai.solver import GeminiQuestionSolver
from auto_answer.ui.console import print_banner, display_answer_terminal, console
from auto_answer.ui.hud import FloatingHUD
from auto_answer.automation.clicker import AutoClicker
from auto_answer.security import redact_secrets


def ensure_debug_dir(config: AppConfig) -> Path:
    out_dir = Path(config.debug_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def do_single_scan(config: AppConfig, solver: GeminiQuestionSolver, clicker: AutoClicker, custom_img: Image.Image = None):
    """Executes a single capture, AI solve, and display cycle."""
    start_time = time.time()

    if custom_img:
        img = custom_img
        console.print("[cyan]🔍 Solving provided test image...[/cyan]")
    else:
        region = config.scan_region
        console.print(
            f"[dim]📸 Capturing screen region ({region.left}, {region.top}, "
            f"{region.width}x{region.height})...[/dim]"
        )
        img = capture_screen_region(region)

        if config.save_debug_screenshots:
            dbg_dir = ensure_debug_dir(config)
            latest_path = dbg_dir / "latest_capture.png"
            img.save(latest_path)
            timestamp = int(time.time())
            dbg_path = dbg_dir / f"scan_{timestamp}.png"
            img.save(dbg_path)

    with console.status("[bold green]🧠 Gemini AI is analyzing the question...[/bold green]", spinner="dots"):
        try:
            result = solver.solve_image(img)
        except Exception as e:
            console.print(f"[bold red]❌ Error from AI Solver:[/bold red] {redact_secrets(e)}")
            return None

    elapsed = time.time() - start_time
    display_answer_terminal(result, elapsed_sec=elapsed)

    # Auto click if enabled
    if not custom_img and config.clicker.enabled:
        clicker.click_option(config.scan_region, result)

    return result


def cmd_snip(args, config: AppConfig):
    """Launch visual snipper to select the emulator question area."""
    console.print("[cyan]✂ Launching Snipping Tool... Drag a box over your emulator question area.[/cyan]")
    region = launch_snipping_tool()
    if region:
        console.print(f"[bold green]✓ Scan region updated: {region.to_tuple()}[/bold green]")
        # Offer immediate test scan
        console.print("[dim]Taking a test capture of the new region...[/dim]")
        img = capture_screen_region(region)
        if config.save_debug_screenshots:
            dbg_dir = ensure_debug_dir(config)
            test_path = dbg_dir / "latest_snip.png"
            img.save(test_path)
            console.print(f"[green]Saved preview to {test_path}[/green]")


def cmd_scan(args, config: AppConfig):
    """Perform a single scan of the configured region."""
    solver = GeminiQuestionSolver(api_key=config.gemini_api_key, model=config.model, demo_mode=getattr(args, "demo", False))
    clicker = AutoClicker(config.clicker)
    do_single_scan(config, solver, clicker)


def cmd_watch(args, config: AppConfig):
    """Interactive loop or timed scanning mode."""
    solver = GeminiQuestionSolver(api_key=config.gemini_api_key, model=config.model, demo_mode=getattr(args, "demo", False))
    clicker = AutoClicker(config.clicker)

    if args.auto:
        console.print(f"[bold yellow]🔄 Auto-scanning every {config.auto_mode_interval_sec} seconds. Press Ctrl+C to stop.[/bold yellow]")
        try:
            while True:
                do_single_scan(config, solver, clicker)
                time.sleep(config.auto_mode_interval_sec)
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopped auto-scan.[/yellow]")
    else:
        console.print("\n[bold cyan]🎮 Interactive Mode Active[/bold cyan]")
        console.print("[dim]Commands: [Enter] = Scan now  |  [s] = Re-snip region  |  [q] = Quit[/dim]\n")
        while True:
            try:
                user_input = input(">> Press [Enter] to scan: ").strip().lower()
                if user_input == "q":
                    console.print("[cyan]Goodbye![/cyan]")
                    break
                elif user_input == "s":
                    cmd_snip(args, config)
                else:
                    do_single_scan(config, solver, clicker)
            except KeyboardInterrupt:
                console.print("\n[yellow]Exiting.[/yellow]")
                break


def cmd_hud(args, config: AppConfig):
    """Launch the floating HUD overlay."""
    solver = GeminiQuestionSolver(api_key=config.gemini_api_key, model=config.model, demo_mode=getattr(args, "demo", False))
    clicker = AutoClicker(config.clicker)

    hud = None

    def on_scan():
        if hud:
            hud.set_status("> STATUS: ANALYZING QUEST...")
            res = do_single_scan(config, solver, clicker)
            if res:
                hud.update_result(res)
            else:
                hud.show_error("Unable to solve the current question")

    def on_snip():
        launch_snipping_tool()
        # Reload config
        cfg = AppConfig.load()
        config.scan_region = cfg.scan_region

    hud = FloatingHUD(config, on_scan_requested=on_scan, on_snip_requested=on_snip)
    console.print("[bold green]✓ Floating HUD launched![/bold green] Drag it near your emulator window.")
    hud.run()


def cmd_live(args, config: AppConfig):
    """Launch autonomous real-time screen scanner."""
    from auto_answer.realtime import RealtimeScanner
    import threading

    solver = GeminiQuestionSolver(api_key=config.gemini_api_key, model=config.model, demo_mode=getattr(args, "demo", False))
    clicker = AutoClicker(config.clicker)

    if getattr(args, "hud", False):
        def on_snip():
            launch_snipping_tool()
            cfg = AppConfig.load()
            config.scan_region = cfg.scan_region

        hud = FloatingHUD(config, on_snip_requested=on_snip)
        scanner = RealtimeScanner(config, solver, clicker, hud=hud)
        hud.on_scan = lambda: scanner.trigger_scan(reason="HUD Button")
        t = threading.Thread(
            target=lambda: scanner.start(auto_detect_changes=not getattr(args, "no_auto_diff", False)),
            daemon=True
        )
        t.start()
        console.print("[bold green]✓ Real-Time Engine + Floating HUD started![/bold green]")
        hud.run()
    else:
        scanner = RealtimeScanner(config, solver, clicker)
        scanner.start(auto_detect_changes=not getattr(args, "no_auto_diff", False))


def cmd_test_sample(args, config: AppConfig):
    """Test the AI solver using the provided sample question image."""
    sample_path = Path("assets/samples/sample_question.png")
    if not sample_path.exists():
        console.print(f"[bold red]❌ Sample image not found at {sample_path}[/bold red]")
        return

    console.print(f"[bold cyan]🧪 Testing with sample image: {sample_path}[/bold cyan]")
    img = Image.open(sample_path)
    solver = GeminiQuestionSolver(api_key=config.gemini_api_key, model=config.model, demo_mode=getattr(args, "demo", False))
    clicker = AutoClicker(config.clicker)
    do_single_scan(config, solver, clicker, custom_img=img)


def cmd_detect_emulator(args, config: AppConfig):
    """Search for running emulator windows."""
    console.print("[cyan]🔍 Searching for emulator windows (BlueStacks, LDPlayer, Nox, etc.)...[/cyan]")
    found = find_emulator_window()
    if found:
        console.print(f"[bold green]✓ Found emulator window: '{found['title']}'[/bold green]")
        b = found["bounds"]
        console.print(f"   Bounds: Left={b.left}, Top={b.top}, Width={b.width}, Height={b.height}")
        console.print("   Tip: Run 'python main.py snip' to precisely select the quiz inner area!")
    else:
        console.print("[yellow]No common emulator window found automatically.[/yellow]")
        console.print("You can use 'python main.py snip' to select any portion of your screen manually.")


def main():
    print_banner()
    config = AppConfig.load()

    parser = argparse.ArgumentParser(
        description="Auto Answer - Screen Scanner & AI Question Solver for Emulators and Quizzes",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--demo", action="store_true", help="Run with simulated AI solver to preview UI and formatting")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # snip
    subparsers.add_parser("snip", help="Launch interactive snipping tool to drag and select screen area")

    # scan
    scan_p = subparsers.add_parser("scan", help="Scan the configured screen area once and display answer")
    scan_p.add_argument("--demo", action="store_true", help="Run in demo mode without calling Gemini API")

    # watch
    watch_p = subparsers.add_parser("watch", help="Continuous / interactive mode (press Enter to scan)")
    watch_p.add_argument("--auto", action="store_true", help="Auto-scan on timer interval instead of keypress")
    watch_p.add_argument("--demo", action="store_true", help="Run in demo mode without calling Gemini API")

    # hud
    hud_p = subparsers.add_parser("hud", help="Launch floating HUD overlay beside your emulator")
    hud_p.add_argument("--demo", action="store_true", help="Run in demo mode without calling Gemini API")

    # live / realtime
    live_p = subparsers.add_parser("live", aliases=["realtime"], help="Autonomous real-time screen scanner with F8 hotkey and auto-detection")
    live_p.add_argument("--hud", action="store_true", help="Launch floating HUD overlay alongside real-time scanner")
    live_p.add_argument("--no-auto-diff", action="store_true", help="Disable automatic scene-change detection (hotkey only)")
    live_p.add_argument("--demo", action="store_true", help="Run in demo mode without calling Gemini API")

    # test-sample
    sample_p = subparsers.add_parser("test-sample", help="Test the AI solver on the sample question image")
    sample_p.add_argument("--demo", action="store_true", help="Run in demo mode without calling Gemini API")

    # detect-emulator
    subparsers.add_parser("detect-emulator", help="Detect emulator window location")

    args = parser.parse_args()

    if not args.command:
        # Default behavior if run without args: real-time live mode
        # Safe default: wait for an explicit scan instead of immediately capturing
        # and uploading the user's screen when the program is opened.
        cmd_watch(argparse.Namespace(auto=False, demo=False), config)
    elif args.command == "snip":
        cmd_snip(args, config)
    elif args.command == "scan":
        cmd_scan(args, config)
    elif args.command == "watch":
        cmd_watch(args, config)
    elif args.command in ("live", "realtime"):
        cmd_live(args, config)
    elif args.command == "hud":
        cmd_hud(args, config)
    elif args.command == "test-sample":
        cmd_test_sample(args, config)
    elif args.command == "detect-emulator":
        cmd_detect_emulator(args, config)


if __name__ == "__main__":
    main()
