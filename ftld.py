import asyncio
import aiodns
import aiohttp
from typing import List, Dict
import itertools
import string
from datetime import datetime
import whois
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ICANN_TLD_LIST_URL = "https://data.iana.org/TLD/tlds-alpha-by-domain.txt"

# TLDs supported by Route 53 and Cloudflare
ROUTE53_TLDS = {
    'ac', 'academy', 'accountants', 'actor', 'adult', 'agency', 'airforce', 'apartments', 'associates', 'auction', 'audio',
    'band', 'bargains', 'beer', 'bet', 'bid', 'bike', 'bingo', 'bio', 'biz', 'black', 'blue', 'boutique', 'builders', 'business', 'buzz',
    'cab', 'cafe', 'camera', 'camp', 'capital', 'cards', 'care', 'careers', 'cash', 'casino', 'catering', 'cc', 'center', 'ceo', 'chat',
    'cheap', 'christmas', 'church', 'city', 'claims', 'cleaning', 'click', 'clinic', 'clothing', 'cloud', 'club', 'coach', 'codes',
    'coffee', 'college', 'com', 'community', 'company', 'computer', 'condos', 'construction', 'consulting', 'contact', 'contractors',
    'cool', 'coupons', 'credit', 'creditcard', 'cruises', 'dance', 'dating', 'deals', 'degree', 'delivery', 'democrat', 'dental',
    'design', 'diamonds', 'diet', 'digital', 'direct', 'directory', 'discount', 'dog', 'domains', 'education', 'email', 'energy',
    'engineering', 'enterprises', 'equipment', 'estate', 'events', 'exchange', 'expert', 'exposed', 'express', 'fail', 'fan', 'farm',
    'finance', 'financial', 'fish', 'fitness', 'flights', 'florist', 'flowers', 'fm', 'football', 'forsale', 'foundation', 'fun',
    'fund', 'furniture', 'futbol', 'fyi', 'gallery', 'games', 'gift', 'gifts', 'gives', 'glass', 'global', 'gmbh', 'gold', 'golf',
    'graphics', 'gratis', 'green', 'gripe', 'group', 'guide', 'guitars', 'guru', 'haus', 'healthcare', 'help', 'hiv', 'hockey',
    'holdings', 'holiday', 'host', 'hosting', 'house', 'im', 'immo', 'immobilien', 'industries', 'info', 'ink', 'institute', 'insure',
    'international', 'investments', 'io', 'irish', 'jewelry', 'juegos', 'kaufen', 'kim', 'kitchen', 'kiwi', 'land', 'law', 'lease',
    'legal', 'lgbt', 'life', 'lighting', 'limited', 'limo', 'link', 'live', 'llc', 'loan', 'loans', 'lol', 'ltd', 'maison', 'management',
    'marketing', 'mba', 'media', 'memorial', 'mobi', 'moda', 'money', 'mortgage', 'movie', 'name', 'net', 'network', 'news', 'ninja',
    'onl', 'online', 'org', 'partners', 'parts', 'photo', 'photography', 'photos', 'pics', 'pictures', 'pink', 'pizza', 'place',
    'plumbing', 'plus', 'poker', 'porn', 'press', 'pro', 'productions', 'properties', 'property', 'pub', 'pw', 'qpon', 'recipes',
    'red', 'reise', 'reisen', 'rentals', 'repair', 'report', 'republican', 'restaurant', 'reviews', 'rip', 'rocks', 'run', 'sale',
    'sarl', 'school', 'schule', 'services', 'sex', 'sexy', 'shiksha', 'shoes', 'shopping', 'show', 'singles', 'site', 'ski', 'soccer',
    'social', 'solar', 'solutions', 'software', 'space', 'store', 'stream', 'studio', 'style', 'sucks', 'supplies', 'supply', 'support',
    'surgery', 'systems', 'tattoo', 'tax', 'taxi', 'team', 'tech', 'technology', 'tennis', 'theater', 'tienda', 'tips', 'tires', 'today',
    'tools', 'tours', 'town', 'toys', 'trade', 'training', 'tv', 'university', 'uno', 'vacations', 'vegas', 'ventures', 'vg', 'viajes',
    'video', 'villas', 'vision', 'vote', 'voyage', 'watch', 'website', 'wedding', 'wiki', 'wine', 'work', 'works', 'world', 'wtf',
    'xyz', 'zone'
}

CLOUDFLARE_TLDS = {
    'academy', 'accountant', 'accountants', 'actor', 'agency', 'apartments', 'app', 'associates', 'attorney', 'auction', 'audio',
    'baby', 'band', 'bar', 'bargains', 'beer', 'bet', 'bid', 'bike', 'bingo', 'biz', 'black', 'blog', 'blue', 'boo', 'boston',
    'boutique', 'broker', 'builders', 'business', 'cab', 'cafe', 'cam', 'camera', 'camp', 'capital', 'cards', 'care', 'careers',
    'casa', 'cash', 'casino', 'catering', 'cc', 'center', 'ceo', 'chat', 'cheap', 'christmas', 'church', 'city', 'claims', 'cleaning',
    'clinic', 'clothing', 'cloud', 'club', 'co', 'co.uk', 'coach', 'codes', 'coffee', 'college', 'com', 'com.co', 'community',
    'company', 'compare', 'computer', 'condos', 'construction', 'consulting', 'contact', 'contractors', 'cooking', 'cool', 'coupons',
    'credit', 'creditcard', 'cricket', 'cruises', 'dad', 'dance', 'date', 'dating', 'day', 'deals', 'degree', 'delivery', 'democrat',
    'dental', 'dentist', 'design', 'dev', 'diamonds', 'diet', 'digital', 'direct', 'directory', 'discount', 'doctor', 'dog', 'domains',
    'download', 'education', 'email', 'energy', 'engineer', 'engineering', 'enterprises', 'equipment', 'esq', 'estate', 'events',
    'exchange', 'expert', 'exposed', 'express', 'fail', 'faith', 'family', 'fans', 'farm', 'fashion', 'finance', 'financial', 'fish',
    'fishing', 'fit', 'fitness', 'flights', 'florist', 'flowers', 'fm', 'foo', 'football', 'forex', 'forsale', 'foundation', 'fun',
    'fund', 'furniture', 'futbol', 'fyi', 'gallery', 'game', 'games', 'garden', 'gifts', 'gives', 'glass', 'gmbh', 'gold', 'golf',
    'graphics', 'gratis', 'green', 'gripe', 'group', 'guide', 'guitars', 'guru', 'haus', 'health', 'healthcare', 'hockey', 'holdings',
    'holiday', 'horse', 'hospital', 'host', 'hosting', 'house', 'how', 'immo', 'immobilien', 'industries', 'info', 'ink', 'institute',
    'insure', 'international', 'investments', 'io', 'irish', 'jetzt', 'jewelry', 'kaufen', 'kim', 'kitchen', 'land', 'lawyer', 'lease',
    'legal', 'lgbt', 'life', 'lighting', 'limited', 'limo', 'live', 'loan', 'loans', 'lol', 'love', 'ltd', 'luxe', 'maison', 'management',
    'market', 'marketing', 'markets', 'mba', 'me', 'me.uk', 'media', 'memorial', 'men', 'miami', 'mobi', 'moda', 'mom', 'money',
    'monster', 'mortgage', 'mov', 'movie', 'net', 'net.co', 'net.uk', 'network', 'new', 'news', 'nexus', 'ninja', 'nom.co', 'observer',
    'online', 'org', 'org.uk', 'page', 'partners', 'parts', 'party', 'pet', 'phd', 'photography', 'photos', 'pics', 'pictures', 'pink',
    'pizza', 'place', 'plumbing', 'plus', 'press', 'pro', 'productions', 'prof', 'promo', 'properties', 'protection', 'pub', 'racing',
    'realty', 'recipes', 'red', 'rehab', 'reise', 'reisen', 'rent', 'rentals', 'repair', 'report', 'republican', 'rest', 'restaurant',
    'review', 'reviews', 'rip', 'rocks', 'rodeo', 'rsvp', 'run', 'sale', 'salon', 'sarl', 'school', 'schule', 'science', 'security',
    'select', 'services', 'shoes', 'shopping', 'show', 'singles', 'site', 'soccer', 'social', 'software', 'solar', 'solutions', 'soy',
    'space', 'storage', 'store', 'stream', 'studio', 'style', 'supplies', 'supply', 'support', 'surf', 'surgery', 'systems', 'tax',
    'taxi', 'team', 'tech', 'technology', 'tennis', 'theater', 'theatre', 'tienda', 'tips', 'tires', 'today', 'tools', 'tours', 'town',
    'toys', 'trade', 'trading', 'training', 'tv', 'uk', 'university', 'us', 'vacations', 'ventures', 'vet', 'viajes', 'video', 'villas',
    'vin', 'vip', 'vision', 'vodka', 'voyage', 'watch', 'webcam', 'website', 'wedding', 'wiki', 'win', 'wine', 'work', 'works', 'world',
    'wtf', 'xyz', 'yoga', 'zone'
}

async def fetch_tlds() -> List[str]:
    async with aiohttp.ClientSession() as session:
        async with session.get(ICANN_TLD_LIST_URL) as response:
            content = await response.text()
            return [tld.lower() for tld in content.split('\n')[1:] if tld]

async def is_available(domain: str, resolver: aiodns.DNSResolver) -> Dict:
    try:
        await resolver.query(domain, 'SOA')
        return {"domain": domain, "status": "registered"}
    except aiodns.error.DNSError:
        return {"domain": domain, "status": "available"}
    except Exception as e:
        logger.error(f"Error checking domain {domain}: {e}")
        return {"domain": domain, "status": "error", "error": str(e)}

def get_whois_info(domain: str) -> Dict:
    try:
        w = whois.whois(domain)
        
        registrant = w.registrant or w.org or "N/A"
        expiration_date = w.expiration_date
        if isinstance(expiration_date, list):
            expiration_date = expiration_date[0]
        expiration_date_str = expiration_date.strftime("%Y-%m-%d") if expiration_date else "N/A"
        
        return {
            "registrant": registrant,
            "expiration_date": expiration_date_str,
            "raw_data": json.dumps(w, default=str, indent=2)
        }
    except Exception as e:
        logger.error(f"Error fetching WHOIS info for {domain}: {e}")
        return {"registrant": "Error", "expiration_date": "Error", "raw_data": str(e)}

async def check_domains(base_domain: str, tlds: List[str], registrar: str) -> List[Dict]:
    resolver = aiodns.DNSResolver()
    tasks = []
    for tld in tlds:
        if registrar == 'route53' and tld not in ROUTE53_TLDS:
            continue
        if registrar == 'cloudflare' and tld not in CLOUDFLARE_TLDS:
            continue
        tasks.append(is_available(f"{base_domain}.{tld}", resolver))
    
    results = []
    total_checked = 0
    for task in asyncio.as_completed(tasks):
        result = await task
        if result['status'] == 'registered':
            retries = 3
            while retries > 0:
                try:
                    whois_info = get_whois_info(result['domain'])
                    result.update(whois_info)
                    break
                except Exception as e:
                    logger.error(f"Error fetching WHOIS info for {result['domain']}: {e}")
                    retries -= 1
                    if retries > 0:
                        logger.info(f"Retrying in 5 seconds... ({retries} attempts left)")
                        await asyncio.sleep(5)
                    else:
                        result.update({
                            "registrant": "Error fetching data",
                            "expiration_date": "Error fetching data",
                            "raw_data": f"Error after 3 attempts: {e}"
                        })
        results.append(result)
        total_checked += 1
        logger.info(f"Checked {total_checked} out of {len(tasks)} domains... Status: {result['status']}")
    
    return results

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

def generate_permutations():
    letters = string.ascii_lowercase
    digits = string.digits
    return [''.join(p) for p in itertools.chain(
        itertools.product(letters, repeat=2),
        itertools.product(digits, repeat=2),
        itertools.product(letters, digits),
        itertools.product(digits, letters)
    )]

async def check_permutations(tld: str) -> List[Dict]:
    resolver = aiodns.DNSResolver()
    permutations = generate_permutations()
    tasks = [is_available(f"{perm}.{tld}", resolver) for perm in permutations]
    
    results = []
    chunk_size = 100  # Adjust this value based on your needs and rate limits
    total_checked = 0
    for i in range(0, len(tasks), chunk_size):
        chunk = tasks[i:i+chunk_size]
        chunk_results = await asyncio.gather(*chunk)
        available = [r for r in chunk_results if r['status'] == 'available']
        results.extend(available)
        total_checked += len(chunk)
        print(f"Checked {total_checked} out of {len(tasks)} permutations... Found {len(results)} available so far.")
    
    return results

def save_to_markdown(results: List[Dict], filename: str, mode: str, tld: str = None):
    with open(filename, 'w') as f:
        f.write(f"# fTLD Domain Availability Check Results\n\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        if mode == "Check specific domain":
            f.write(f"## Checked Domains\n\n")
            for result in results:
                f.write(f"### {result['domain']}\n")
                f.write(f"- Status: **{result['status']}**\n")
                if result['status'] == 'registered':
                    f.write(f"- Registrant: {result['registrant']}\n")
                    f.write(f"- Expiration Date: {result['expiration_date']}\n")
                    f.write(f"- Raw RDAP Data:\n```json\n{result['raw_data']}\n```\n")
                f.write("\n")
        elif mode == "Find available 2-character domains":
            f.write(f"## Available 2-character domains for .{tld}\n\n")
            for result in results:
                f.write(f"- {result['domain']}\n")
        
        f.write(f"\n## Summary\n\n")
        available_count = sum(1 for r in results if r['status'] == 'available')
        f.write(f"- Total domains checked: {len(results)}\n")
        f.write(f"- Available domains: {available_count}\n")
        f.write(f"- Registered domains: {len(results) - available_count}\n")

async def main():
    print("Welcome to fTLD!")

    save_option = input("Do you want to save the results to a file? (y/n): ").lower()
    filename = None
    if save_option == 'y':
        filename = input("Enter the filename to save (without extension): ")
        filename = f"{filename}.md"

    mode_options = ["Check specific domain", "Find available 2-character domains"]
    mode_choice = get_user_choice("Select a mode:", mode_options)

    results = []

    if mode_choice == "Check specific domain":
        registrar_options = ["All TLDs", "Route 53", "Cloudflare"]
        registrar_choice = get_user_choice("Select a registrar or TLD option:", registrar_options)
        
        registrar = None
        if registrar_choice == "Route 53":
            registrar = "route53"
        elif registrar_choice == "Cloudflare":
            registrar = "cloudflare"

        base_domain = input("Enter the domain name to check (without TLD): ").lower()

        tlds = await fetch_tlds()
        results = await check_domains(base_domain, tlds, registrar)
        
        available = [r for r in results if r['status'] == 'available']
        
        print(f"\nAvailable domains:")
        for domain in available:
            print(f"- {domain['domain']}")
        
        print(f"\nRegistered domains:")
        for domain in [r for r in results if r['status'] == 'registered']:
            print(f"- {domain['domain']} (Registrant: {domain['registrant']}, Expires: {domain['expiration_date']})")
        
        print(f"\nTotal available domains: {len(available)}")
        print(f"Total registered domains: {len(results) - len(available)}")

    elif mode_choice == "Find available 2-character domains":
        tld = input("Enter the TLD to check (e.g., com, net, org): ").lower()
        print(f"Checking all 2-character permutations for .{tld}")
        
        results = await check_permutations(tld)
        
        print(f"\nAvailable 2-character domains for .{tld}:")
        for domain in results:
            print(f"- {domain['domain']}")
        
        print(f"\nTotal available 2-character domains: {len(results)}")

    if filename:
        save_to_markdown(results, filename, mode_choice, tld if mode_choice == "Find available 2-character domains" else None)
        print(f"Results saved to {filename}")

if __name__ == "__main__":
    asyncio.run(main())
