import asyncio
import aiodns
from typing import List, Dict
from datetime import datetime, timedelta

ICANN_TLD_LIST_URL = "https://data.iana.org/TLD/tlds-alpha-by-domain.txt"

async def fetch_tlds() -> List[str]:
    import aiohttp
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

async def check_domains(base_domain: str, tlds: List[str]) -> List[Dict]:
    resolver = aiodns.DNSResolver()
    tasks = [is_available(f"{base_domain}.{tld}", resolver) for tld in tlds]
    return await asyncio.gather(*tasks)

async def main():
    base_domain = input("Enter the domain name to check (without TLD): ").lower()
    tlds = await fetch_tlds()
    
    results = await check_domains(base_domain, tlds)
    
    available = [r for r in results if r['status'] == 'available']
    
    print(f"\nAvailable domains:")
    for domain in available:
        print(f"- {domain['domain']}")
    
    print(f"\nTotal available domains: {len(available)}")

if __name__ == "__main__":
    asyncio.run(main())
