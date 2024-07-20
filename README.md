# fTLD - Find Top Level Domain

fTLD is a Python script that allows you to check domain availability across multiple Top Level Domains (TLDs) or find available domains of a specific length for a given TLD.

## Features

- Check domain availability across all TLDs or filter by specific registrars
- Find available domains of a specific length for a given TLD
- Fetch WHOIS information for registered domains
- Save results to a Markdown file

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Gyarbij/ftld.git
   cd ftld
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv ftld_env
   source ftld_env/bin/activate  # On Windows, use: ftld_env\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script with:

```bash
python ftld.py
```

Follow the interactive prompts to:

1. Choose whether to save results to a file
2. Select the mode of operation:
   - Check specific domain
   - Find available N-character domains
3. If checking a specific domain:
   - Select a registrar filter
   - Enter the domain name to check (without TLD)
4. If finding available N-character domains:
   - Enter the TLD to check
   - Specify the number of characters

## Example Output

The script will display results in the console and optionally save them to a Markdown file. The output includes:

- Detailed results for each domain checked
- Summary of available, registered, unknown, and error statuses
- For N-character domain searches, a list of available domains

## Dependencies

- aiodns
- aiohttp
- python-whois

## Notes

- The script uses asynchronous operations to improve performance when checking multiple domains.
- WHOIS lookups are performed for registered domains to fetch additional information.
- Rate limiting may be applied to avoid overloading DNS servers or WHOIS services.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
