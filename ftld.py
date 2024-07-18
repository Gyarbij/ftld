import asyncio
import aiodns
import aiohttp
from typing import List, Dict

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

async def check_domains(base_domain: str, tlds: List[str], registrar: str) -> List[Dict]:
    resolver = aiodns.DNSResolver()
    tasks = []
    for tld in tlds:
        if registrar == 'route53' and tld not in ROUTE53_TLDS:
            continue
        if registrar == 'cloudflare' and tld not in CLOUDFLARE_TLDS:
            continue
        tasks.append(is_available(f"{base_domain}.{tld}", resolver))
    return await asyncio.gather(*tasks)

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
    print("Welcome to the Domain Availability Checker!")

    # Registrar selection
    registrar_options = ["All TLDs", "Route 53", "Cloudflare"]
    registrar_choice = get_user_choice("Select a registrar or TLD option:", registrar_options)
    
    registrar = None
    if registrar_choice == "Route 53":
        registrar = "route53"
    elif registrar_choice == "Cloudflare":
        registrar = "cloudflare"

    # Domain name input
    base_domain = input("Enter the domain name to check (without TLD): ").lower()

    # Fetch TLDs and check domains
    tlds = await fetch_tlds()
    results = await check_domains(base_domain, tlds, registrar)
    
    available = [r for r in results if r['status'] == 'available']
    
    print(f"\nAvailable domains:")
    for domain in available:
        print(f"- {domain['domain']}")
    
    print(f"\nTotal available domains: {len(available)}")

if __name__ == "__main__":
    asyncio.run(main())
