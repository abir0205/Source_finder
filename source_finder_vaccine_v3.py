#!/usr/bin/env python3
"""
Vaccine Information Source Finder v2.0
Systematically searches for validated vaccine information from authoritative sources
using WHO Vaccine Safety Net criteria and peer-reviewed research
"""

import requests
from urllib.parse import quote_plus
import json
from datetime import datetime
from typing import Dict, List, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class VaccineSourceFinder:
    """Find validated vaccine information from reputable sources using systematic criteria"""

    # ============================================================================
    # SOURCE QUALITY CRITERIA
    # ============================================================================
    # Based on WHO Vaccine Safety Net evaluation criteria:
    # 1. Credibility: Transparent ownership, management, and funding
    # 2. Content: Evidence-based, scientifically accurate, peer-reviewed
    # 3. Accessibility: Clear, up-to-date, easy to navigate
    # 4. Independence: No pharmaceutical industry conflicts of interest

    # ============================================================================
    # TIER 1: INTERNATIONAL & GOVERNMENT HEALTH AUTHORITIES
    # ============================================================================
    # These sources have:
    # - Public health mandates
    # - Extensive research capabilities
    # - Peer review processes
    # - Public accountability
    # - No commercial conflicts of interest

    GOVERNMENT_AGENCIES = {
        'CDC': {
            'name': 'Centers for Disease Control and Prevention (USA)',
            'main': 'https://www.cdc.gov/vaccines/index.html',
            'search': 'https://search.cdc.gov/search/',
            'direct_links': {
                'Vaccines & Immunizations': 'https://www.cdc.gov/vaccines/index.html',
                'Vaccine-Preventable Diseases': 'https://www.cdc.gov/vaccines/vpd/vaccines-diseases.html',
                'Immunization Schedules': 'https://www.cdc.gov/vaccines/schedules/index.html',
                'ACIP Recommendations': 'https://www.cdc.gov/acip/index.html'
            },
            'quality_indicators': ['Government agency', 'Peer-reviewed', 'Evidence-based']
        },
        'WHO': {
            'name': 'World Health Organization',
            'main': 'https://www.who.int/health-topics/vaccines-and-immunization',
            'search': 'https://www.who.int/search',
            'direct_links': {
                'Vaccines & Immunization': 'https://www.who.int/health-topics/vaccines-and-immunization',
                'Immunization Team': 'https://www.who.int/teams/immunization-vaccines-and-biologicals',
                'Q&A on Vaccines': 'https://www.who.int/news-room/questions-and-answers/item/vaccines-and-immunization',
                'Vaccine Safety Net': 'https://www.vaccinesafetynet.org/'
            },
            'quality_indicators': ['International authority', 'WHO-validated', 'Evidence-based']
        },
        'FDA': {
            'name': 'U.S. Food and Drug Administration',
            'main': 'https://www.fda.gov/vaccines-blood-biologics/vaccines',
            'direct_links': {
                'Vaccines Homepage': 'https://www.fda.gov/vaccines-blood-biologics/vaccines',
                'Vaccine Safety': 'https://www.fda.gov/vaccines-blood-biologics/safety-availability-biologics',
                'Vaccine Approvals': 'https://www.fda.gov/vaccines-blood-biologics/approved-products'
            },
            'quality_indicators': ['Regulatory authority', 'Clinical trial oversight', 'Safety monitoring']
        },
        'NIH': {
            'name': 'National Institutes of Health',
            'main': 'https://www.niaid.nih.gov/research/vaccines',
            'direct_links': {
                'Vaccine Research': 'https://www.niaid.nih.gov/research/vaccines',
                'Clinical Trials': 'https://clinicaltrials.gov/'
            },
            'quality_indicators': ['Research institution', 'Clinical trials', 'Peer-reviewed']
        }
    }

    # ============================================================================
    # TIER 2: WHO VACCINE SAFETY NET MEMBERS
    # ============================================================================
    # Pre-validated websites meeting WHO's 34 quality criteria

    VSN_MEMBERS = {
        'Immunization Action Coalition': {
            'url': 'https://www.immunize.org/',
            'description': 'Educational resources for healthcare professionals and public',
            'languages': ['English', 'Spanish', 'Multiple'],
            'vsn_validated': True
        },
        'VaccineInformation.org': {
            'url': 'https://www.vaccineinformation.org/',
            'description': 'Public-friendly vaccine information',
            'languages': ['English'],
            'vsn_validated': True
        },
        'CHOP Vaccine Education Center': {
            'url': 'https://www.chop.edu/centers-programs/vaccine-education-center',
            'description': "Children's Hospital of Philadelphia expert resources",
            'languages': ['English'],
            'vsn_validated': True
        },
        'Johns Hopkins Institute for Vaccine Safety': {
            'url': 'https://www.hopkinsvaccine.org/',
            'description': 'Independent vaccine safety research and information',
            'languages': ['English'],
            'vsn_validated': True
        },
        'Immunize Canada': {
            'url': 'https://immunize.ca/',
            'description': 'Canadian immunization information',
            'languages': ['English', 'French'],
            'vsn_validated': True
        }
    }

    # ============================================================================
    # TIER 3: PEER-REVIEWED MEDICAL DATABASES
    # ============================================================================
    # For accessing primary scientific research

    MEDICAL_DATABASES = {
        'PubMed': {
            'url': 'https://pubmed.ncbi.nlm.nih.gov/',
            'api_base': 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/',
            'description': 'Free database of peer-reviewed medical literature',
            'search_url': 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi',
            'summary_url': 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi',
            'article_url_template': 'https://pubmed.ncbi.nlm.nih.gov/{pmid}/'
        },
        'PubMed Central': {
            'url': 'https://www.ncbi.nlm.nih.gov/pmc/',
            'description': 'Free full-text archive of biomedical literature',
            'access': 'Free full-text articles'
        },
        'Cochrane Library': {
            'url': 'https://www.cochranelibrary.com/',
            'description': 'Systematic reviews of medical research',
            'focus': 'Evidence-based medicine'
        }
    }

    # ============================================================================
    # TIER 4: PEER-REVIEWED JOURNALS
    # ============================================================================
    # Specialized vaccine research journals

    PEER_REVIEWED_JOURNALS = {
        'Vaccine': {
            'url': 'https://www.sciencedirect.com/journal/vaccine',
            'publisher': 'Elsevier',
            'description': 'Leading journal in vaccinology',
            'impact': 'High-impact',
            'peer_reviewed': True
        },
        'npj Vaccines': {
            'url': 'https://www.nature.com/npjvaccines/',
            'publisher': 'Nature',
            'description': 'Open-access vaccine research',
            'impact': 'High-impact',
            'peer_reviewed': True,
            'open_access': True
        },
        'Expert Review of Vaccines': {
            'url': 'https://www.tandfonline.com/journals/ierv20',
            'publisher': 'Taylor & Francis',
            'description': 'Expert commentary on vaccine development',
            'peer_reviewed': True,
            'medline_indexed': True
        },
        'Human Vaccines & Immunotherapeutics': {
            'url': 'https://www.tandfonline.com/journals/khvi20',
            'publisher': 'Taylor & Francis',
            'description': 'International vaccinology research',
            'peer_reviewed': True,
            'open_access': True
        },
        'The Lancet': {
            'url': 'https://www.thelancet.com/',
            'publisher': 'Elsevier',
            'description': 'Premier general medical journal',
            'impact': 'Very high-impact',
            'peer_reviewed': True
        },
        'New England Journal of Medicine': {
            'url': 'https://www.nejm.org/',
            'publisher': 'Massachusetts Medical Society',
            'description': 'Leading medical journal',
            'impact': 'Very high-impact',
            'peer_reviewed': True
        },
        'JAMA': {
            'url': 'https://jamanetwork.com/',
            'publisher': 'American Medical Association',
            'description': 'Journal of the American Medical Association',
            'impact': 'Very high-impact',
            'peer_reviewed': True
        },
        'BMJ': {
            'url': 'https://www.bmj.com/',
            'publisher': 'BMJ Publishing Group',
            'description': 'British Medical Journal',
            'impact': 'High-impact',
            'peer_reviewed': True
        }
    }

    # ============================================================================
    # TIER 5: PROFESSIONAL MEDICAL ORGANIZATIONS
    # ============================================================================

    PROFESSIONAL_ORGS = {
        'American Academy of Pediatrics': {
            'url': 'https://www.aap.org/immunization',
            'description': 'Pediatric immunization guidance',
            'audience': 'Healthcare professionals and families'
        },
        'Infectious Diseases Society of America': {
            'url': 'https://www.idsociety.org/',
            'description': 'Infectious disease expertise',
            'audience': 'Healthcare professionals'
        },
        'Vaccines.gov': {
            'url': 'https://www.vaccines.gov/',
            'description': 'U.S. government vaccine information portal',
            'audience': 'General public'
        }
    }

    # ============================================================================
    # SOURCE EVALUATION CRITERIA
    # ============================================================================

    QUALITY_CRITERIA = {
        'credibility': [
            'Transparent ownership and management',
            'Clear funding sources disclosed',
            'Expert authorship and editorial oversight',
            'Established organizational reputation'
        ],
        'content': [
            'Evidence-based information',
            'Peer-reviewed when applicable',
            'Regular updates and review',
            'References to scientific studies'
        ],
        'independence': [
            'No pharmaceutical industry conflicts',
            'No commercial bias',
            'Public health mission'
        ],
        'accessibility': [
            'Clear and understandable language',
            'Easy navigation',
            'Available in multiple languages (when possible)',
            'Mobile-friendly'
        ]
    }

    def __init__(
            self,
            session: requests.Session | None = None,
            timeout: int = 10,
            user_agent: str = "VaccineFinder/2.0 (+https://example.org)",
            pubmed_tool: str = "vaccine_finder",
            pubmed_email: str = "you@example.org",
    ):
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self.timeout = timeout
        self.pubmed_common = {"tool": pubmed_tool, "email": pubmed_email}

        retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)

    # ============================================================================
    # PUBMED SEARCH METHODS
    # ============================================================================

    def search_pubmed(
            self,
            query: str,
            max_results: int = 10,
            sort: str = "relevance",  # or "pub_date"
            retstart: int = 0,
            mindate: str | None = None,  # "2020"
            maxdate: str | None = None,  # "2025"
            datetype: str = "edat",  # edat|pdat
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

    def _fetch_pubmed_details(self, pmids: list[str], include_abstract: bool = False) -> list[dict]:
        """Fetch details for PubMed articles"""
        pmids = list(dict.fromkeys(pmids))  # dedupe, keep order
        if not pmids: return []

        params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "json", **self.pubmed_common}
        try:
            r = self.session.get(self.MEDICAL_DATABASES["PubMed"]["summary_url"], params=params, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
        except requests.exceptions.RequestException:
            return []

        out, result = [], data.get("result", {})
        for pmid in pmids:
            a = result.get(pmid) or {}
            authors = [au.get("name") for au in a.get("authors", []) if "name" in au]
            out.append({
                "pmid": pmid,
                "title": a.get("title") or "No title",
                "authors": authors,
                "journal": a.get("source") or "Unknown",
                "pubdate": a.get("pubdate") or "Unknown",
                "url": self.MEDICAL_DATABASES["PubMed"]["article_url_template"].format(pmid=pmid),
                "quality_tier": "Tier 3: Peer-Reviewed Database",
            })
        return out


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
            "version": "2.0.1",
            "search_methodology": "WHO VSN criteria",
            "sources": sources,
            "quality_criteria": self.QUALITY_CRITERIA,
            "provenance": {"pubmed_sort": pubmed_sort, "mindate": mindate, "maxdate": maxdate},
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
                    author_names = [a.get('name', '') for a in article['authors'][:3]]
                    authors_str = ', '.join(author_names)
                    if len(article['authors']) > 3:
                        authors_str += ', et al.'
                    print(f"   Authors: {authors_str}")
                print(f"   Journal: {article['source']}")
                print(f"   Published: {article['pubdate']}")
                print(f"   URL: {article['url']}")
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

    def export_source_guide(self, filename: str = "vaccine_source_guide.json"):
        """
        Export a complete guide to trusted sources

        Args:
            filename: Output filename
        """
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

        with open(filename, 'w') as f:
            json.dump(guide, f, indent=2)

        print(f"✓ Source guide exported to: {filename}")


def main():
    """Main function with interactive menu"""
    finder = VaccineSourceFinder()

    print("=" * 70)
    print("VACCINE INFORMATION SOURCE FINDER v2.0")
    print("=" * 70)
    print("\nSystematic approach to finding trusted vaccine information")
    print("Based on WHO Vaccine Safety Net quality criteria\n")

    while True:
        print("\nOPTIONS:")
        print("1. Search for vaccine information by topic")
        print("2. View all trusted sources by tier")
        print("3. View WHO Vaccine Safety Net members")
        print("4. View quality evaluation criteria")
        print("5. Export complete source guide (JSON)")
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
            finder.export_source_guide(filename)

        elif choice == '6':
            print("\nThank you for using Vaccine Information Source Finder!")
            print("Remember: Always consult healthcare professionals for medical decisions.")
            break

        else:
            print("\n❌ Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
