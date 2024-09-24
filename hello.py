from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from datetime import datetime, timezone
from rich import print as rprint  # For rich printing
from rich.traceback import install
import os
import time

install(show_locals=True)

# Define user agent and current date for file naming
uA = "Mozilla/5.0 (Linux; Android 11; Redmi Note 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36"
c_d = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
timeout_duration = 10000  # 10 seconds (Playwright uses milliseconds)


def read_urls_from_file(file_path):
    """
    Reads URLs from a file, assuming they are comma-separated.

    Args:
        file_path (str): The path to the file containing URLs.

    Returns:
        list: A list of URLs, or an empty list if the file could not be read.
    """
    try:
        with open(file_path, "r") as file:
            data = file.read().strip()
            if not data:
                rprint("[bold red]Error: The file is empty.[/bold red]")
                return []
            return [url.strip() for url in data.split(",") if url.strip()]
    except FileNotFoundError:
        rprint(f"[bold red]Error: File not found at {file_path}[/bold red]")
        return []
    except Exception as e:
        rprint(f"[bold red]Error reading file: {e}[/bold red]")
        return []


def rename_video_file(video_path, destination_path):
    """
    Rename a video file from the specified path to the destination path.

    Args:
        video_path (str): The path to the video file to be renamed.
        destination_path (str): The desired path for the renamed video file.

    Returns:
        bool: True if the file was successfully renamed, False otherwise.
    """
    try:
        os.rename(video_path, destination_path)
        return True
    except FileNotFoundError:
        rprint(f"[bold red]Error: Video file not found: {video_path}[/bold red]")
        return False
    except Exception as e:
        rprint(f"[bold red]Error renaming video file: {e}[/bold red]")
        return False


def main_function(urls):
    """Main function to visit websites and handle video recording."""
    if not urls:
        rprint("[bold red]Error: No URLs provided.[/bold red]")
        return

    rprint("[bold magenta]Starting Playwright Script...[/bold magenta]")
    with sync_playwright() as p:
        rprint("[bold cyan]Launching Chromium Browser...[/bold cyan]")
        br1 = p.chromium.launch()

        rprint("[bold green]Creating a new browser context...[/bold green]")
        context = br1.new_context(
            record_video_dir="clicks/",
            record_video_size={"width": 640, "height": 480},
            user_agent=uA,
            locale="de-DE",
            timezone_id="Europe/Berlin",
        )

        try:
            rprint("[bold yellow]Looping through URLs...[/bold yellow]")
            for pageVisit in urls:
                if not pageVisit.startswith("http"):
                    rprint(f"[bold red]Skipping invalid URL: {pageVisit}[/bold red]")
                    continue

                rprint(f"[bold blue]Visiting URL: {pageVisit}...[/bold blue]")

                # Create a new page
                page1 = context.new_page()

                try:
                    # Visit the page with a timeout
                    page1.goto(pageVisit, timeout=timeout_duration)

                    # Extract the domain name from the URL
                    domain = pageVisit.split("//")[-1].split("/")[0]

                    rprint(
                        f"[bold cyan]Taking screenshot of {pageVisit}...[/bold cyan]"
                    )
                    # Create screenshot - with current date time and domain name
                    page1.screenshot(path=f"clicks/{c_d}-{domain}.png", full_page=True)

                    # Wait for the video file to be created
                    video_file = page1.video.path()

                    # Renaming the video file after page closure
                    destination_path = f"clicks/{c_d}-{domain}.webm"
                    if rename_video_file(video_file, destination_path):
                        rprint(
                            f"[bold green]Renamed video file for {pageVisit}...[/bold green]"
                        )
                    else:
                        rprint(
                            f"[bold red]Failed to rename video file for {pageVisit}...[/bold red]"
                        )
                except PlaywrightTimeoutError:
                    rprint(
                        f"[bold red]Timeout exceeded for {pageVisit}. Skipping...[/bold red]"
                    )

                finally:
                    # Close the page after processing
                    page1.close()

        finally:
            rprint("[bold yellow]Closing browser context and browser...[/bold yellow]")
            # Close the context and browser
            context.close()
            br1.close()
            os.system("ls -al clicks/")

        rprint("[bold magenta]Done![/bold magenta]")


if __name__ == "__main__":
    # Change 'urls.txt' to the path where your URL list is stored.
    file_path = "urls.txt"

    rprint(f"[bold cyan]Reading URLs from: {file_path}[/bold cyan]")
    urls = read_urls_from_file(file_path)

    if urls:
        rprint(f"[bold green]Found {len(urls)} URLs to visit.[/bold green]")
    main_function(urls)
