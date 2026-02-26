import requests
import os
import traceback

# VirusTotal API Key (Free tier allows 4 requests per minute)
# In a real environment, load this from python-dotenv or environment variables
VT_API_KEY = os.environ.get("VT_API_KEY", "YOUR_VIRUSTOTAL_API_KEY") 

def scan_hash_virustotal(sha256_hash: str):
    """
    Queries the VirusTotal API (v3) with a file's SHA-256 hash.
    Returns whether the file is considered malicious to prevent zero-day attacks.
    """
    # If no real API key is provided, we simulate a clean response 
    # so the app doesn't break for demonstration purposes.
    if VT_API_KEY == "YOUR_VIRUSTOTAL_API_KEY" or not VT_API_KEY:
        print("[VIRUSTOTAL] No API key configured. Bypassing real scan (Simulated Clean).")
        return {
            "is_malware": False,
            "malicious_votes": 0,
            "total_engines": 0,
            "report_link": None,
            "error": "No API Key"
        }

    url = f"https://www.virustotal.com/api/v3/files/{sha256_hash}"
    headers = {
        "accept": "application/json",
        "x-apikey": VT_API_KEY
    }

    try:
        print(f"[VIRUSTOTAL] Pinging global threat intelligence for hash: {sha256_hash}...")
        response = requests.get(url, headers=headers, timeout=10)
        
        # 404 means the file hash is unknown to VirusTotal (Likely safe/new)
        if response.status_code == 404:
            return {
                "is_malware": False,
                "malicious_votes": 0,
                "total_engines": 0,
                "report_link": None,
                "note": "Hash not found in VT database."
            }
            
        response.raise_for_status()
        data = response.json()
        
        # Extract analysis stats
        stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
        malicious = stats.get("malicious", 0)
        suspicious = stats.get("suspicious", 0)
        undetected = stats.get("undetected", 0)
        harmless = stats.get("harmless", 0)
        
        total_engines = malicious + suspicious + undetected + harmless
        
        # Threat intelligence logic:
        # If 3 or more anti-virus engines flag it as malicious, we quarantine it.
        is_malware = malicious >= 3
        
        vt_link = f"https://www.virustotal.com/gui/file/{sha256_hash}"
        
        return {
            "is_malware": is_malware,
            "malicious_votes": malicious,
            "total_engines": total_engines,
            "report_link": vt_link
        }

    except requests.exceptions.HTTPError as http_err:
        print(f"[VIRUSTOTAL API ERROR] {http_err}")
        return {"is_malware": False, "error": str(http_err)}
    except Exception as e:
        traceback.print_exc()
        return {"is_malware": False, "error": str(e)}
