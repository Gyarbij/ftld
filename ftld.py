import asyncio
import aiodns
import aiohttp
import whois
from typing import List, Dict
import itertools
import string
from datetime import datetime
import logging
import json
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ICANN_TLD_LIST_URL = "https://data.iana.org/TLD/tlds-alpha-by-domain.txt"
REGISTRAR_TLD_BASE_URL = "https://externe.blob.core.windows.net/ftld"
REGISTRARS = ["All TLDs", "Route 53", "Cloudflare", "Azure", "Namecheap", "SquareSpace", "GoDaddy"]

async def fetch_tlds(url: str) -> List[str]:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            content = await response.text()
            return list(set([tld.lower().strip() for tld in content.split('\n') if tld.strip() and not tld.startswith('#')]))

async def fetch_registrar_tlds(registrar: str) -> List[str]:
    registrar_url = registrar.lower().replace(' ', '')
    url = f"{REGISTRAR_TLD_BASE_URL}/{registrar_url}.txt"
    return await fetch_tlds(url)

async def is_available(domain: str, resolver: aiodns.DNSResolver) -> Dict:
    try:
        await resolver.query(domain, 'NS')
        return {"domain": domain, "status": "registered"}
    except aiodns.error.DNSError as e:
        if 'NXDOMAIN' in str(e):
            # Double-check with a socket connection
            try:
                socket.gethostbyname(domain)
                return {"domain": domain, "status": "registered"}
            except socket.gaierror:
                return {"domain": domain, "status": "available"}
        else:
            return {"domain": domain, "status": "unknown", "error": str(e)}
    except Exception as e:
        logger.error(f"Error checking domain {domain}: {e}")
        return {"domain": domain, "status": "error", "error": str(e)}

def get_whois_info(domain: str) -> Dict:
    try:
        w = whois.whois(domain)
        
        if not w.domain_name:
            return {"status": "available"}

        result = {
            "status": "registered",
            "registrant": w.registrant or w.org or "N/A",
            "expiration_date": "N/A",
            "creation_date": "N/A",
            "last_updated": "N/A",
            "name_servers": [],
        }

        for date_field in ['expiration_date', 'creation_date', 'updated_date']:
            date_value = getattr(w, date_field)
            if date_value:
                if isinstance(date_value, list):
                    date_value = date_value[0]
                result[date_field.replace('updated_date', 'last_updated')] = date_value.strftime("%Y-%m-%d") if hasattr(date_value, 'strftime') else str(date_value)

        if w.name_servers:
            result["name_servers"] = w.name_servers if isinstance(w.name_servers, list) else [w.name_servers]

        result["raw_data"] = json.dumps(w, default=str, indent=2)
        return result
    except whois.parser.PywhoisError:
        return {"status": "available"}
    except Exception as e:
        logger.error(f"Error fetching WHOIS info for {domain}: {e}")
        return {"status": "error", "error": str(e)}

async def check_domains(base_domain: str, tlds: List[str], registrar: str) -> List[Dict]:
    resolver = aiodns.DNSResolver()
    tasks = []
    
    if registrar != "All TLDs":
        filtered_tlds = await fetch_registrar_tlds(registrar)
        tlds = [tld for tld in tlds if tld in filtered_tlds]

    for tld in tlds:
        tasks.append(is_available(f"{base_domain}.{tld}", resolver))
    
    results = []
    total_checked = 0
    for task in asyncio.as_completed(tasks):
        result = await task
        if result['status'] in ['registered', 'unknown']:
            retries = 3
            while retries > 0:
                try:
                    whois_info = get_whois_info(result['domain'])
                    if whois_info['status'] == 'registered':
                        result.update(whois_info)
                        break
                    elif whois_info['status'] == 'available':
                        result['status'] = 'available'
                        break
                except Exception as e:
                    logger.error(f"Error fetching WHOIS info for {result['domain']}: {e}")
                    retries -= 1
                    if retries > 0:
                        logger.info(f"Retrying in 5 seconds... ({retries} attempts left)")
                        await asyncio.sleep(5)
                    else:
                        result.update({
                            "status": "unknown",
                            "error": f"Error after 3 attempts: {e}"
                        })
        results.append(result)
        total_checked += 1
        logger.info(f"Checked {total_checked} out of {len(tasks)} domains... Status: {result['status']}")
    
    return results

def generate_permutations(n: int) -> List[str]:
    chars = string.ascii_lowercase + string.digits
    return [''.join(p) for p in itertools.product(chars, repeat=n)]

async def check_permutations(tld: str, n: int, progress_callback) -> List[Dict]:
    resolver = aiodns.DNSResolver()
    permutations = generate_permutations(n)
    tasks = [check_domain(f"{perm}.{tld}", resolver) for perm in permutations]
    
    results = []
    chunk_size = 100  # Adjust this value based on your needs and rate limits
    for i in range(0, len(tasks), chunk_size):
        chunk = tasks[i:i+chunk_size]
        chunk_results = await asyncio.gather(*chunk)
        results.extend(chunk_results)
        await progress_callback(i + chunk_size, len(tasks), chunk_results[-1])
    
    return results

def save_to_markdown(results: List[Dict], filename: str, mode: str, base_domain: str = None, tld: str = None, n: int = None):
    with open(filename, 'w') as f:
        f.write(f"# Domain Availability Check Results\n\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        if mode == "Check specific domain":
            f.write(f"## Checked Domains for '{base_domain}'\n\n")
            for result in results:
                f.write(f"### {result['domain']}\n")
                f.write(f"- Status: **{result['status']}**\n")
                if result['status'] == 'registered':
                    f.write(f"- Registrant: {result.get('registrant', 'N/A')}\n")
                    f.write(f"- Creation Date: {result.get('creation_date', 'N/A')}\n")
                    f.write(f"- Expiration Date: {result.get('expiration_date', 'N/A')}\n")
                    f.write(f"- Last Updated: {result.get('last_updated', 'N/A')}\n")
                    f.write(f"- Name Servers: {', '.join(result.get('name_servers', []) or ['N/A'])}\n")
                elif result['status'] == 'error':
                    f.write(f"- Error: {result.get('error', 'Unknown error')}\n")
                f.write("\n")
        elif mode == "Find available N-character domains":
            f.write(f"## Available {n}-character domains for .{tld}\n\n")
            for result in results:
                if result['status'] == 'available':
                    f.write(f"- {result['domain']}\n")
        
        f.write(f"\n## Summary\n\n")
        available_count = sum(1 for r in results if r['status'] == 'available')
        registered_count = sum(1 for r in results if r['status'] == 'registered')
        unknown_count = sum(1 for r in results if r['status'] == 'unknown')
        error_count = sum(1 for r in results if r['status'] == 'error')
        f.write(f"- Total domains checked: {len(results)}\n")
        f.write(f"- Available domains: {available_count}\n")
        f.write(f"- Registered domains: {registered_count}\n")
        f.write(f"- Unknown status: {unknown_count}\n")
        f.write(f"- Errors: {error_count}\n")

async def progress_reporter(current: int, total: int, last_result: Dict):
    progress = current / total
    bar_length = 50
    filled_length = int(bar_length * progress)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    
    sys.stdout.write(f'\r[{bar}] {current}/{total} - {last_result["domain"]} ({last_result["status"]})')
    sys.stdout.flush()
    
    if current == total:
        print()  # New line after completion

def get_user_choice(prompt: str, options: List[str]) -> str:
    while True:
        print(prompt)
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")
        try:
            choice = int(input("Enter your choice (number): "))
            if 1 <= choice <= len(options):
                return options[choice - 1]
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

async def main():
    print("Welcome to fTLD - Find Top Level Domain!")

    save_option = input("Do you want to save the results to a file? (y/N): ").lower()
    filename = None
    if save_option == 'y':
        filename = input("Enter the filename to save (without extension): ")
        filename = f"{filename}.md"

    mode_options = ["Check specific domain", "Find available N-character domains"]
    mode_choice = get_user_choice("Select a mode:", mode_options)

    results = []

    if mode_choice == "Check specific domain":
        registrar_choice = get_user_choice("Select a registrar filter:", REGISTRARS)
        
        tlds = await fetch_tlds(ICANN_TLD_LIST_URL)

        base_domain = input("Enter the domain name to check (without TLD): ").lower()

        print(f"Checking {base_domain} across TLDs...")
        results = await check_domains(base_domain, tlds, registrar_choice)
        
        available = [r for r in results if r['status'] == 'available']
        registered = [r for r in results if r['status'] == 'registered']
        unknown = [r for r in results if r['status'] == 'unknown']
        errors = [r for r in results if r['status'] == 'error']
        
        print(f"\nDetailed results for {base_domain}:")
        for result in results:
            print(f"- {result['domain']}:")
            print(f"  Status: {result['status']}")
            if result['status'] == 'registered':
                print(f"  Registrant: {result.get('registrant', 'N/A')}")
                print(f"  Creation Date: {result.get('creation_date', 'N/A')}")
                print(f"  Expiration Date: {result.get('expiration_date', 'N/A')}")
                print(f"  Last Updated: {result.get('last_updated', 'N/A')}")
                print(f"  Name Servers: {', '.join(result.get('name_servers', []) or ['N/A'])}")
            elif result['status'] == 'error':
                print(f"  Error: {result.get('error', 'Unknown error')}")
            print()

        print(f"\nTotal available domains: {len(available)}")
        print(f"Total registered domains: {len(registered)}")
        print(f"Total unknown status: {len(unknown)}")
        print(f"Total errors: {len(errors)}")
        print(f"Total checked domains: {len(results)}")

    elif mode_choice == "Find available N-character domains":
        tld = input("Enter the TLD to check (e.g., com, net, org): ").lower()
        n = int(input("Enter the number of characters to check (e.g., 2 for ho.nl, ab.io, etc.): "))
        print(f"Checking all {n}-character permutations for .{tld}")
        
        results = await check_permutations(tld, n, progress_reporter)
        available = [r for r in results if r['status'] == 'available']
        
        print(f"\nAvailable {n}-character domains for .{tld}:")
        for domain in available:
            print(f"- {domain['domain']}")
        
        print(f"\nTotal available {n}-character domains: {len(available)}")

    if filename:
        save_to_markdown(results, filename, mode_choice, 
                         base_domain if mode_choice == "Check specific domain" else None,
                         tld if mode_choice == "Find available N-character domains" else None,
                         n if mode_choice == "Find available N-character domains" else None)
        print(f"Results saved to {filename}")

if __name__ == "__main__":
    asyncio.run(main())
