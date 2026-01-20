#!/usr/bin/env python3
"""
Vaccine Information Source Finder v4
Systematically searches for validated vaccine information from authoritative sources
using WHO Vaccine Safety Net criteria and peer-reviewed research

Changes from v2.1:
- Now loads source data from JSON files in resources/ folder
- Change 1: Added input validation to __init__ (timeout and email)
- Change 4: Added statistics to comprehensive_search results
- Change 5: Fixed author display bug in display_results
- Change 6: Added multiple export formats (JSON, CSV, HTML, Markdown)
"""

import requests
from urllib.parse import quote_plus
import json
from datetime import datetime
from typing import Dict, List, Optional
import re
import csv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pathlib import Path
import os


class VaccineSourceFinder:
    """Find validated vaccine information from reputable sources using systematic criteria"""

    def __init__(
            self,
            session: requests.Session | None = None,
            timeout: int = 10,
            user_agent: str = "VaccineFinder/4 (+https://example.org)",
            pubmed_tool: str = "vaccine_finder",
            pubmed_email: str = "you@example.org",
            resources_dir: str = "resources"
    ):
        """
        Initialize the Vaccine Source Finder
        
        Args:
            session: Optional custom requests session
            timeout: Request timeout in seconds (default: 10)
            user_agent: User agent string for requests
            pubmed_tool: Tool identifier for PubMed API
            pubmed_email: Email for PubMed API identification
            resources_dir: Directory containing JSON source files (default: "resources")
            
        Raises:
            ValueError: If timeout is not positive or email is invalid
            FileNotFoundError: If resources directory or required files are missing
        """
        # Input validation
        if timeout <= 0:
            raise ValueError("Timeout must be positive")
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", pubmed_email):
            raise ValueError("Invalid email format for PubMed API")
        
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self.timeout = timeout
        self.pubmed_common = {"tool": pubmed_tool, "email": pubmed_email}

        retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)

        # Load source data from JSON files
        self.resources_dir = Path(resources_dir)
        self._load_resources()

    def _load_resources(self):
        """Load all source data from JSON files in resources directory"""
        if not self.resources_dir.exists():
            raise FileNotFoundError(
                f"Resources directory not found: {self.resources_dir}\n"
                f"Please create it and add the required JSON files."
            )

        required_files = {
            'GOVERNMENT_AGENCIES.json': 'GOVERNMENT_AGENCIES',
            'VSN_MEMBERS.json': 'VSN_MEMBERS',
            'MEDICAL_DATABASES.json': 'MEDICAL_DATABASES',
            'PEER_REVIEWED_JOURNALS.json': 'PEER_REVIEWED_JOURNALS',
            'PROFESSIONAL_ORGS.json': 'PROFESSIONAL_ORGS',
            'QUALITY_CRITERIA.json': 'QUALITY_CRITERIA'
        }

        for filename, attr_name in required_files.items():
            file_path = self.resources_dir / filename
            
            if not file_path.exists():
                raise FileNotFoundError(
                    f"Required file not found: {file_path}\n"
                    f"Please ensure all source JSON files are in the resources directory."
                )
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    setattr(self, attr_name, data)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in {filename}: {e}")
            except Exception as e:
                raise Exception(f"Error loading {filename}: {e}")

        print(f"✓ Loaded source data from {self.resources_dir}")

    # ============================================================================
    # PUBMED SEARCH METHODS
    # ============================================================================

    def search_pubmed(
            self,
            query: str,
            max_results: int = 10,
            sort: str = "relevance",
            retstart: int = 0,
            mindate: str | None = None,
            maxdate: str | None = None,
            datetype: str = "edat",
    ) -> list[dict]:
        """
        Search PubMed for peer-reviewed vaccine research
        Uses the free NCBI E-utilities API

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of article dictionaries with metadata
        """
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retstart": retstart,
            "retmode": "json",
            "sort": sort, **self.pubmed_common
        }

        if mindate: params["mindate"] = mindate
        if maxdate: params["maxdate"] = maxdate
        if mindate or maxdate: params["datetype"] = datetype

        try:
            r = self.session.get(self.MEDICAL_DATABASES["PubMed"]["search_url"], params=params, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
        except requests.exceptions.RequestException:
            return []

        pmids = data.get("esearchresult", {}).get("idlist", [])
        return self._fetch_pubmed_details(pmids) if pmids else []

    def _fetch_pubmed_details(
            self,
            pmids: List[str],
            include_abstract: bool = False,
            batch_size: int = 200
    ) -> List[Dict]:
        """
        Fetch details for PubMed articles with batch processing

        Args:
            pmids: List of PubMed IDs
            include_abstract: Whether to fetch full abstracts
            batch_size: Number of PMIDs per API request (max 200)

        Returns:
            List of article dictionaries with metadata
        """
        pmids = list(dict.fromkeys(pmids))
        if not pmids:
            return []

        all_results = []

        for i in range(0, len(pmids), batch_size):
            batch = pmids[i:i + batch_size]

            params = {
                "db": "pubmed",
                "id": ",".join(batch),
                "retmode": "json",
                **self.pubmed_common
            }

            try:
                r = self.session.get(
                    self.MEDICAL_DATABASES["PubMed"]["summary_url"],
                    params=params,
                    timeout=self.timeout
                )
                r.raise_for_status()
                data = r.json()

                result = data.get("result", {})
                for pmid in batch:
                    if pmid not in result:
                        continue

                    a = result[pmid]
                    authors = [au.get("name") for au in a.get("authors", []) if "name" in au]

                    article = {
                        "pmid": pmid,
                        "title": a.get("title") or "No title",
                        "authors": authors,
                        "journal": a.get("source") or "Unknown",
                        "pubdate": a.get("pubdate") or "Unknown",
                        "url": self.MEDICAL_DATABASES["PubMed"]["article_url_template"].format(pmid=pmid),
                        "quality_tier": "Tier 3: Peer-Reviewed Database",
                    }

                    if "elocationid" in a:
                        article["doi"] = a["elocationid"]
                    if "volume" in a:
                        article["volume"] = a["volume"]
                    if "issue" in a:
                        article["issue"] = a["issue"]
                    if "pages" in a:
                        article["pages"] = a["pages"]

                    all_results.append(article)

            except requests.exceptions.RequestException as e:
                print(f"⚠️  Error fetching batch starting at index {i}: {e}")
                continue

        return all_results

    # ============================================================================
    # GOVERNMENT AGENCY METHODS
    # ============================================================================

    def search_government_agencies(self, topic: str, query_prefix: str = "vaccines") -> dict:
        """
        Generate search information for government health agencies

        Args:
            topic: Search topic

        Returns:
            Dictionary of agency search URLs and direct links
        """
        results = {}

        query = f"{query_prefix} {topic}".strip()
        for code, info in self.GOVERNMENT_AGENCIES.items():
            base = info.get("search")
            search_url = None
            if base:
                if code == "CDC":
                    search_url = f"{base}?query={quote_plus(query)}&sitelimit=cdc.gov"
                else:
                    search_url = f"{base}?query={quote_plus(query)}"
            results[code] = {
                "name": info.get("name", code),
                "search_url": search_url,
                "main_url": info.get("main"),
                "direct_links": info.get("direct_links", {}),
                "quality_indicators": info.get("quality_indicators", []),
                "quality_tier": "Tier 1: Government/International Authority",
                "terms": query,
            }
        return results

    # ============================================================================
    # VSN MEMBERS METHODS
    # ============================================================================

    def get_vsn_members(self, language: str | None = None) -> dict:
        """
        Get WHO Vaccine Safety Net validated members

        Returns:
            Dictionary of VSN-validated websites
        """
        members = {}
        for name, info in sorted(self.VSN_MEMBERS.items(), key=lambda kv: kv[0].lower()):
            if language and language not in info.get("languages", []):
                continue
            members[name] = {
                **info,
                "quality_tier": "Tier 2: WHO Vaccine Safety Net Validated",
                "validation": "Meets WHO 34-point quality criteria",
            }
        return members

    # ============================================================================
    # COMPREHENSIVE SEARCH
    # ============================================================================

    def comprehensive_search(
            self,
            topic: str,
            pubmed_results: int = 10,
            include_tier1: bool = True,
            include_tier2: bool = True,
            include_pubmed: bool = True,
            pubmed_sort: str = "relevance",
            mindate: str | None = None,
            maxdate: str | None = None,
    ) -> dict:
        """
        Perform a comprehensive search across all trusted source tiers

        Args:
            topic: Search topic
            pubmed_results: Number of PubMed results to retrieve

        Returns:
            Dictionary containing categorized search results
        """
        sources: dict = {}
        if include_tier1:
            sources["government_agencies"] = self.search_government_agencies(topic)
        if include_tier2:
            sources["vsn_members"] = self.get_vsn_members()
        if include_pubmed:
            sources["pubmed"] = self.search_pubmed(
                f"vaccine {topic}", max_results=pubmed_results, sort=pubmed_sort, mindate=mindate, maxdate=maxdate
            )
        sources["peer_reviewed_journals"] = {k: {**v, "quality_tier": "Tier 4"} for k, v in
                                             self.PEER_REVIEWED_JOURNALS.items()}
        sources["professional_organizations"] = {k: {**v, "quality_tier": "Tier 5"} for k, v in
                                                 self.PROFESSIONAL_ORGS.items()}
        sources["medical_databases"] = {k: {**v, "quality_tier": "Tier 3"} for k, v in self.MEDICAL_DATABASES.items()}

        return {
            "topic": topic,
            "timestamp": datetime.now().isoformat(),
            "version": "4",
            "search_methodology": "WHO VSN criteria",
            "sources": sources,
            "quality_criteria": self.QUALITY_CRITERIA,
            "provenance": {"pubmed_sort": pubmed_sort, "mindate": mindate, "maxdate": maxdate},
            "statistics": {
                "total_sources": sum(
                    len(v) if isinstance(v, (list, dict)) else 0
                    for v in sources.values()
                ),
                "pubmed_articles": len(sources.get("pubmed", [])),
                "tiers_included": sum([include_tier1, include_tier2, include_pubmed])
            }
        }

    # ============================================================================
    # DISPLAY METHODS
    # ============================================================================

    def display_results(self, results: Dict):
        """Display search results in a readable, tiered format"""
        print("\n" + "=" * 70)
        print("SEARCH RESULTS - ORGANIZED BY SOURCE QUALITY TIER")
        print("=" * 70)

        # Tier 1: Government Agencies
        if 'government_agencies' in results['sources']:
            print("\n" + "🏛️  TIER 1: GOVERNMENT & INTERNATIONAL HEALTH AUTHORITIES")
            print("-" * 70)
            print("Highest credibility - Public health mandate, peer-reviewed, no conflicts")
            print()

            for agency, info in results['sources']['government_agencies'].items():
                print(f"\n{info['name']} ({agency})")
                print(f"   Quality Indicators: {', '.join(info['quality_indicators'])}")
                print(f"   Main URL: {info['main_url']}")
                if info.get('search_url'):
                    print(f"   Search: {info['search_url']}")
                print(f"   Direct Resources:")
                for link_name, link_url in info['direct_links'].items():
                    print(f"      • {link_name}: {link_url}")

        # Tier 2: VSN Members
        if 'vsn_members' in results['sources']:
            print("\n" + "✅ TIER 2: WHO VACCINE SAFETY NET VALIDATED SOURCES")
            print("-" * 70)
            print("Pre-validated by WHO using 34 quality criteria")
            print()

            for name, info in results['sources']['vsn_members'].items():
                print(f"\n{name}")
                print(f"   URL: {info['url']}")
                print(f"   Description: {info['description']}")
                print(f"   Languages: {', '.join(info['languages'])}")
                print(f"   ✓ WHO Vaccine Safety Net Member")

        # Tier 3: PubMed Results
        if 'pubmed' in results['sources'] and results['sources']['pubmed']:
            print("\n" + "📚 TIER 3: PEER-REVIEWED RESEARCH (PubMed)")
            print("-" * 70)
            print("Primary scientific literature - peer-reviewed studies")
            print()

            for i, article in enumerate(results['sources']['pubmed'], 1):
                print(f"\n{i}. {article['title']}")
                if article.get('authors'):
                    authors = article['authors']
                    if isinstance(authors, list) and authors:
                        author_names = authors[:3]
                        authors_str = ', '.join(author_names)
                        if len(authors) > 3:
                            authors_str += ', et al.'
                        print(f"   Authors: {authors_str}")
                print(f"   Journal: {article['journal']}")
                print(f"   Published: {article['pubdate']}")
                print(f"   URL: {article['url']}")
                if 'doi' in article:
                    print(f"   DOI: {article['doi']}")
                print(f"   Type: Peer-reviewed scientific article")

        # Tier 4: Journals
        if 'peer_reviewed_journals' in results['sources']:
            print("\n" + "📖 TIER 4: PEER-REVIEWED JOURNALS")
            print("-" * 70)
            print("Leading medical journals for in-depth research")
            print()

            for name, info in results['sources']['peer_reviewed_journals'].items():
                access = " (Open Access)" if info.get('open_access') else ""
                print(f"   • {name}{access}")
                print(f"     {info['description']} - {info['url']}")

        # Tier 5: Professional Organizations
        if 'professional_organizations' in results['sources']:
            print("\n" + "🏥 TIER 5: PROFESSIONAL MEDICAL ORGANIZATIONS")
            print("-" * 70)
            print("Expert guidance from medical professional societies")
            print()

            for name, info in results['sources']['professional_organizations'].items():
                print(f"   • {name}")
                print(f"     {info['description']} - {info['url']}")

        # Quality Criteria
        print("\n" + "📋 SOURCE EVALUATION CRITERIA")
        print("-" * 70)
        print("All sources are evaluated based on WHO Vaccine Safety Net criteria:")
        print()

        for category, criteria in results.get('quality_criteria', {}).items():
            print(f"{category.upper()}:")
            for criterion in criteria:
                print(f"   ✓ {criterion}")

        print("\n" + "=" * 70)
        print("IMPORTANT REMINDERS")
        print("=" * 70)
        print("• Always cross-reference information across multiple sources")
        print("• Prioritize Tier 1 & 2 sources for most reliable information")
        print("• Check publication dates - use most recent information")
        print("• Consult healthcare professionals for personal medical decisions")
        print("• Be skeptical of sources not listed in these tiers")
        print("=" * 70 + "\n")

        # Display statistics
        if 'statistics' in results:
            print("SEARCH STATISTICS")
            print("=" * 70)
            print(f"Total sources found: {results['statistics']['total_sources']}")
            print(f"PubMed articles: {results['statistics']['pubmed_articles']}")
            print(f"Tiers searched: {results['statistics']['tiers_included']}")
            print("=" * 70 + "\n")

    # ============================================================================
    # EXPORT METHODS
    # ============================================================================

    def export_source_guide(
            self,
            filename: str = "vaccine_source_guide.json",
            format: str = "json"
    ):
        """
        Export a complete guide to trusted sources

        Args:
            filename: Output filename
            format: Export format - "json", "csv", "html", "markdown"
        """
        # Validate format
        supported_formats = ["json", "csv", "html", "markdown"]
        if format not in supported_formats:
            print(f"❌ Unsupported format '{format}'. Using 'json' instead.")
            format = "json"

        guide = {
            'title': 'Trusted Vaccine Information Sources Guide',
            'created': datetime.now().isoformat(),
            'methodology': 'Based on WHO Vaccine Safety Net criteria',
            'quality_tiers': {
                'tier_1': {
                    'name': 'Government & International Health Authorities',
                    'description': 'Highest credibility - public health mandate, peer-reviewed, no conflicts',
                    'sources': self.GOVERNMENT_AGENCIES
                },
                'tier_2': {
                    'name': 'WHO Vaccine Safety Net Validated',
                    'description': 'Pre-validated by WHO using 34 quality criteria',
                    'sources': self.VSN_MEMBERS
                },
                'tier_3': {
                    'name': 'Medical Databases',
                    'description': 'Access to peer-reviewed literature',
                    'sources': self.MEDICAL_DATABASES
                },
                'tier_4': {
                    'name': 'Peer-Reviewed Journals',
                    'description': 'Leading medical journals',
                    'sources': self.PEER_REVIEWED_JOURNALS
                },
                'tier_5': {
                    'name': 'Professional Organizations',
                    'description': 'Expert guidance from medical societies',
                    'sources': self.PROFESSIONAL_ORGS
                }
            },
            'quality_criteria': self.QUALITY_CRITERIA
        }

        # Ensure filename has correct extension
        if not filename.endswith(f'.{format}'):
            filename = filename.rsplit('.', 1)[0] + f'.{format}'

        if format == "json":
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(guide, f, indent=2, ensure_ascii=False)

        elif format == "csv":
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Tier', 'Tier Name', 'Source Name', 'URL', 'Description'])

                for tier_key, tier_data in guide['quality_tiers'].items():
                    tier_num = tier_key.replace('tier_', '')
                    tier_name = tier_data['name']

                    for source_name, source_data in tier_data['sources'].items():
                        url = source_data.get('url') or source_data.get('main', '')
                        description = source_data.get('description', '')
                        writer.writerow([tier_num, tier_name, source_name, url, description])

        elif format == "markdown":
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("# Trusted Vaccine Information Sources Guide\n\n")
                f.write(f"**Created:** {guide['created']}\n\n")
                f.write(f"**Methodology:** {guide['methodology']}\n\n")
                f.write("---\n\n")

                for tier_key, tier_data in guide['quality_tiers'].items():
                    f.write(f"## {tier_data['name']}\n\n")
                    f.write(f"*{tier_data['description']}*\n\n")

                    for source_name, source_data in tier_data['sources'].items():
                        f.write(f"### {source_name}\n\n")
                        url = source_data.get('url') or source_data.get('main', '')
                        if url:
                            f.write(f"**URL:** [{url}]({url})\n\n")
                        if 'description' in source_data:
                            f.write(f"**Description:** {source_data['description']}\n\n")
                        f.write("---\n\n")

        elif format == "html":
            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trusted Vaccine Information Sources Guide</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; border-left: 4px solid #3498db; padding-left: 10px; }}
        h3 {{ color: #7f8c8d; }}
        .tier {{ margin: 20px 0; padding: 15px; background: #ecf0f1; border-radius: 5px; }}
        .source {{ margin: 15px 0; padding: 10px; background: white; border-radius: 5px; border-left: 3px solid #3498db; }}
        a {{ color: #3498db; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>Trusted Vaccine Information Sources Guide</h1>
    <p><strong>Created:</strong> {guide['created']}</p>
    <p><strong>Methodology:</strong> {guide['methodology']}</p>
"""

            for tier_key, tier_data in guide['quality_tiers'].items():
                html_content += f"""
    <div class="tier">
        <h2>{tier_data['name']}</h2>
        <p><em>{tier_data['description']}</em></p>
"""
                for source_name, source_data in tier_data['sources'].items():
                    url = source_data.get('url') or source_data.get('main', '')
                    html_content += f"""
        <div class="source">
            <h3>{source_name}</h3>
"""
                    if url:
                        html_content += f'            <p><strong>URL:</strong> <a href="{url}" target="_blank">{url}</a></p>\n'
                    if 'description' in source_data:
                        html_content += f'            <p><strong>Description:</strong> {source_data["description"]}</p>\n'
                    html_content += "        </div>\n"
                html_content += "    </div>\n"

            html_content += """
</body>
</html>
"""
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)

        print(f"✓ Source guide exported to: {filename} (format: {format})")


def main():
    """Main function with interactive menu"""
    
    # Determine resources directory path
    # Check if running from script directory or if resources is in current directory
    script_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
    resources_dir = script_dir / "resources"
    
    # If resources not found next to script, check current directory
    if not resources_dir.exists():
        resources_dir = Path.cwd() / "resources"
    
    try:
        finder = VaccineSourceFinder(resources_dir=str(resources_dir))
    except (FileNotFoundError, ValueError) as e:
        print(f"\n❌ Error initializing Vaccine Source Finder:")
        print(f"   {e}")
        print(f"\nPlease ensure the 'resources' directory exists with these files:")
        print("   - GOVERNMENT_AGENCIES.json")
        print("   - VSN_MEMBERS.json")
        print("   - MEDICAL_DATABASES.json")
        print("   - PEER_REVIEWED_JOURNALS.json")
        print("   - PROFESSIONAL_ORGS.json")
        print("   - QUALITY_CRITERIA.json")
        return 1

    print("=" * 70)
    print("VACCINE INFORMATION SOURCE FINDER v4")
    print("=" * 70)
    print("\nSystematic approach to finding trusted vaccine information")
    print("Based on WHO Vaccine Safety Net quality criteria\n")

    while True:
        print("\nOPTIONS:")
        print("1. Search for vaccine information by topic")
        print("2. View all trusted sources by tier")
        print("3. View WHO Vaccine Safety Net members")
        print("4. View quality evaluation criteria")
        print("5. Export complete source guide")
        print("6. Exit")

        choice = input("\nEnter your choice (1-6): ").strip()

        if choice == '1':
            topic = input("\nEnter vaccine topic to search: ").strip()
            if topic:
                results = finder.comprehensive_search(topic)
                finder.display_results(results)

                save = input("\nSave results to JSON file? (y/n): ").strip().lower()
                if save == 'y':
                    filename = f"vaccine_search_{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(filename, 'w') as f:
                        json.dump(results, f, indent=2)
                    print(f"✓ Results saved to: {filename}")

        elif choice == '2':
            print("\n" + "=" * 70)
            print("TRUSTED VACCINE INFORMATION SOURCES - BY TIER")
            print("=" * 70)

            print("\n🏛️  TIER 1: Government & International Health Authorities")
            print("-" * 70)
            for name, info in finder.GOVERNMENT_AGENCIES.items():
                print(f"\n{info['name']} ({name})")
                print(f"   {info['main']}")

            print("\n✅ TIER 2: WHO Vaccine Safety Net Validated")
            print("-" * 70)
            for name, info in finder.VSN_MEMBERS.items():
                print(f"\n{name}")
                print(f"   {info['url']}")

            print("\n📚 TIER 3: Medical Databases")
            print("-" * 70)
            for name, info in finder.MEDICAL_DATABASES.items():
                print(f"\n{name}: {info['url']}")

            print("\n📖 TIER 4: Peer-Reviewed Journals")
            print("-" * 70)
            for name, info in finder.PEER_REVIEWED_JOURNALS.items():
                print(f"\n{name}: {info['url']}")

            print("\n🏥 TIER 5: Professional Organizations")
            print("-" * 70)
            for name, info in finder.PROFESSIONAL_ORGS.items():
                print(f"\n{name}: {info['url']}")

        elif choice == '3':
            vsn = finder.get_vsn_members()
            print("\n" + "=" * 70)
            print("WHO VACCINE SAFETY NET MEMBERS")
            print("=" * 70)
            print("\nThese websites have been validated by WHO using 34 quality criteria")
            print("including credibility, content quality, and independence.\n")

            for name, info in vsn.items():
                print(f"\n{name}")
                print(f"   URL: {info['url']}")
                print(f"   Description: {info['description']}")
                print(f"   Languages: {', '.join(info['languages'])}")
                print(f"   ✓ {info['validation']}")

        elif choice == '4':
            print("\n" + "=" * 70)
            print("SOURCE QUALITY EVALUATION CRITERIA")
            print("=" * 70)
            print("\nBased on WHO Vaccine Safety Net standards:")
            print()

            for category, criteria in finder.QUALITY_CRITERIA.items():
                print(f"\n{category.upper()}:")
                for criterion in criteria:
                    print(f"   ✓ {criterion}")

            print("\n" + "=" * 70)
            print("HOW TO EVALUATE SOURCES:")
            print("=" * 70)
            print("✓ Check: Is the author a trained expert in the field?")
            print("✓ Check: Is the information peer-reviewed?")
            print("✓ Check: Does the organization have a proven track record?")
            print("✓ Check: Are funding sources disclosed?")
            print("✓ Check: Are there conflicts of interest?")
            print("✓ Check: Is the information current and regularly updated?")
            print("✓ Red flag: Single opinions without peer review")
            print("✓ Red flag: Commercial or pharmaceutical industry funding")
            print("✓ Red flag: Emotional appeals without scientific evidence")

        elif choice == '5':
            filename = input("\nEnter filename (default: vaccine_source_guide.json): ").strip()
            if not filename:
                filename = "vaccine_source_guide.json"
            
            print("\nAvailable formats:")
            print("1. JSON (default)")
            print("2. CSV")
            print("3. HTML")
            print("4. Markdown")
            format_choice = input("Choose format (1-4): ").strip()
            
            format_map = {'1': 'json', '2': 'csv', '3': 'html', '4': 'markdown'}
            export_format = format_map.get(format_choice, 'json')
            
            finder.export_source_guide(filename, format=export_format)

        elif choice == '6':
            print("\nThank you for using Vaccine Information Source Finder!")
            print("Remember: Always consult healthcare professionals for medical decisions.")
            break

        else:
            print("\n❌ Invalid choice. Please try again.")

    return 0


if __name__ == "__main__":
    exit(main())
