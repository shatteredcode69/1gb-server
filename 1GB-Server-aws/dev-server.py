from app.main import app
from colorama import init, Fore, Style
import os
import time

init()

def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    banner = f"""
{Fore.CYAN}{'='*70}
{Fore.YELLOW}
 ██╗ ██████╗ ██████╗     ███████╗███████╗██████╗ ██╗   ██╗███████╗██████╗ 
███║██╔════╝ ██╔══██╗    ██╔════╝██╔════╝██╔══██╗██║   ██║██╔════╝██╔══██╗
╚██║██║  ███╗██████╔╝    ███████╗█████╗  ██████╔╝██║   ██║█████╗  ██████╔╝
 ██║██║   ██║██╔══██╗    ╚════██║██╔══╝  ██╔══██╗╚██╗ ██╔╝██╔══╝  ██╔══██╗
 ██║╚██████╔╝██████╔╝    ███████║███████╗██║  ██║ ╚████╔╝ ███████╗██║  ██║
 ╚═╝ ╚═════╝ ╚═════╝     ╚══════╝╚══════╝╚═╝  ╚═╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝
{Fore.CYAN}
    🚀 THE 1GB SERVER 🚀
    Production System on Just 1GB RAM
{Fore.CYAN}{'='*70}{Style.RESET_ALL}
"""
    print(banner)
    
def print_info():
    print(f"{Fore.GREEN}👨‍💻 Developer:{Style.RESET_ALL} Muhammad Abbas")
    print(f"{Fore.GREEN}🎯 Mission:{Style.RESET_ALL} Build Production System on 1GB RAM")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")

def print_urls():
    print(f"{Fore.YELLOW}📡 Server URLs:{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}➜{Style.RESET_ALL} Home:       {Fore.CYAN}http://localhost:5000{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}➜{Style.RESET_ALL} Dashboard:  {Fore.CYAN}http://localhost:5000/dashboard{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}➜{Style.RESET_ALL} Docs:       {Fore.CYAN}http://localhost:5000/docs{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}➜{Style.RESET_ALL} Health:     {Fore.CYAN}http://localhost:5000/api/v1/health{Style.RESET_ALL}")
    print(f"\n{Fore.YELLOW}🎮 Controls:{Style.RESET_ALL}")
    print(f"  {Fore.RED}Press CTRL+C to stop the server{Style.RESET_ALL}\n")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")

def loading_animation():
    print(f"{Fore.YELLOW}🔄 Starting server", end="")
    for _ in range(3):
        time.sleep(0.3)
        print(".", end="", flush=True)
    print(f" {Fore.GREEN}✓{Style.RESET_ALL}\n")

if __name__ == '__main__':
    try:
        print_banner()
        print_info()
        loading_animation()
        print_urls()
        print(f"{Fore.GREEN}✨ Server is running! Open your browser now.{Style.RESET_ALL}\n")
        
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
        
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}👋 Server stopped gracefully. Goodbye!{Style.RESET_ALL}\n")
    except Exception as e:
        print(f"\n{Fore.RED}❌ Error: {e}{Style.RESET_ALL}\n")
