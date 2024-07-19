# fTLD

To use fTLD, follow these steps:

1. Clone repo:
    ```bash
    git clone https://github/Gyarbij/ftld.git
    cd ftld
    ```

2. Virtual Environment: Consider using a virtual environment to isolate the dependencies for the project. This can help avoid conflicts between different versions of libraries. You can create a virtual environment using:

    ```
    python3 -m venv ftld
    source ftld/bin/activate
    ```

3. Install the required dependencies if you haven't already:
   ```
   pip install -r requirements.txt
   ```
4. Run the script with various options:

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
