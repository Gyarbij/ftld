# fTLD

To use fTLD, follow these steps:

1. Clone repo:
    ```bash
    git clone https://github/Gyarbij/ftld.git
    cd ftld
    ```
2. Install the required dependencies if you haven't already:
   ```
   pip install aiodns aiohttp
   ```
3. Run the script with various options:

   - Basic usage (checks all TLDs):
     ```
     python ftld.py example
     ```

   - Filter by Route 53 supported TLDs:
     ```
     python ftld.py example --registrar route53
     ```

   - Filter by Cloudflare supported TLDs:
     ```
     python ftld.py example --registrar cloudflare
