import httpx
from typing import List, Dict, Optional

class ArchPackageService:
    """Service to interact with Arch Linux official repository"""
    
    ARCH_API_BASE = "https://archlinux.org/packages/search/json/"
    
    async def search_packages(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for packages in official Arch repos"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.ARCH_API_BASE,
                    params={"name": query}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])[:limit]
                    
                    return [{
                        "name": pkg.get("pkgname"),
                        "version": pkg.get("pkgver"),
                        "description": pkg.get("pkgdesc"),
                        "repo": pkg.get("repo"),
                        "arch": pkg.get("arch"),
                        "url": f"https://archlinux.org/packages/{pkg.get('repo')}/{pkg.get('arch')}/{pkg.get('pkgname')}/",
                        "last_update": pkg.get("last_update")
                    } for pkg in results]
                
                return []
        except Exception as e:
            print(f"Error searching packages: {e}")
            return []
    
    async def get_package_details(self, repo: str, arch: str, name: str) -> Optional[Dict]:
        """Get detailed information about a specific package"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"https://archlinux.org/packages/{repo}/{arch}/{name}/json/"
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "name": data.get("pkgname"),
                        "version": data.get("pkgver"),
                        "description": data.get("pkgdesc"),
                        "url": data.get("url"),
                        "licenses": data.get("licenses", []),
                        "groups": data.get("groups", []),
                        "depends": data.get("depends", []),
                        "conflicts": data.get("conflicts", []),
                        "provides": data.get("provides", []),
                        "packager": data.get("packager"),
                        "build_date": data.get("build_date"),
                        "last_update": data.get("last_update"),
                        "flag_date": data.get("flag_date"),
                        "compressed_size": data.get("compressed_size"),
                        "installed_size": data.get("installed_size")
                    }
                
                return None
        except Exception as e:
            print(f"Error getting package details: {e}")
            return None

    def format_package_list(self, packages: List[Dict]) -> str:
        """Format package list for LLM response"""
        if not packages:
            return "No packages found."
        
        result = "**Arch Packages Found:**\n\n"
        for pkg in packages:
            result += f"- **{pkg['name']}** ({pkg['version']}) - {pkg['repo']}/{pkg['arch']}\n"
            result += f"  {pkg['description']}\n"
            result += f"  [Package Info]({pkg['url']})\n\n"
        
        return result
