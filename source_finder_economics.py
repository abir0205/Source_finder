#!/usr/bin/env python3
"""
Credible Economic Source Finder
Searches for and ranks credible sources on economic topics
"""

import requests
import json
from typing import List, Dict, Tuple
from datetime import datetime
import argparse


class CredibleSourceFinder:
    """Find and rank credible sources for economic topics"""

    # Highly credible domains for economic research
    TIER_1_DOMAINS = {
        'nber.org': 'National Bureau of Economic Research',
        'imf.org': 'International Monetary Fund',
        'worldbank.org': 'World Bank',
        'oecd.org': 'OECD',
        'federalreserve.gov': 'Federal Reserve',
        'bls.gov': 'Bureau of Labor Statistics',
        'bea.gov': 'Bureau of Economic Analysis',
        'census.gov': 'US Census Bureau',
        'treasury.gov': 'US Treasury',
        'bis.org': 'Bank for International Settlements',
    }

    TIER_2_DOMAINS = {
        'brookings.edu': 'Brookings Institution',
        'piie.com': 'Peterson Institute',
        'cgdev.org': 'Center for Global Development',
        'aeaweb.org': 'American Economic Association',
        'jstor.org': 'JSTOR',
        'sciencedirect.com': 'ScienceDirect',
        'springer.com': 'Springer',
        'wiley.com': 'Wiley',
        'cambridge.org': 'Cambridge University Press',
        'oxfordjournals.org': 'Oxford Journals',
    }

    TIER_3_DOMAINS = {
        'economist.com': 'The Economist',
        'ft.com': 'Financial Times',
        'wsj.com': 'Wall Street Journal',
        'bloomberg.com': 'Bloomberg',
        'reuters.com': 'Reuters',
        'cnbc.com': 'CNBC',
    }

    def __init__(self):
        self.api_url = "https://api.anthropic.com/v1/messages"

    def search_sources(self, topic: str, max_results: int = 10) -> List[Dict]:
        """
        Search for sources on a given economic topic
        Note: This is a template - you'd integrate with actual search APIs
        """
        print(f"\n🔍 Searching for credible sources on: {topic}")
        print("=" * 60)

        # Search queries to try
        queries = [
            f"{topic} site:nber.org OR site:imf.org OR site:worldbank.org",
            f"{topic} academic research paper",
            f"{topic} policy analysis site:brookings.edu OR site:piie.com",
            f"{topic} site:federalreserve.gov OR site:bls.gov",
        ]

        results = []

        # In a real implementation, you would:
        # 1. Use a search API (Google Custom Search, Bing, etc.)
        # 2. Parse the results
        # 3. Filter and rank them

        print("\nTo use this script with live search results, you would need to:")
        print("1. Add a search API key (Google Custom Search, Bing, etc.)")
        print("2. Install required packages: pip install requests")
        print("3. Uncomment and configure the search API integration below")

        return results

    def evaluate_source(self, url: str, title: str = "", description: str = "") -> Tuple[int, str, List[str]]:
        """
        Evaluate the credibility of a source
        Returns: (credibility_score, tier_name, reasons)
        """
        url_lower = url.lower()
        reasons = []

        # Check domain credibility
        for domain, name in self.TIER_1_DOMAINS.items():
            if domain in url_lower:
                reasons.append(f"Tier 1 source: {name}")
                reasons.append("Official government or international organization")
                return 100, "Tier 1 (Highest)", reasons

        for domain, name in self.TIER_2_DOMAINS.items():
            if domain in url_lower:
                reasons.append(f"Tier 2 source: {name}")
                reasons.append("Academic or reputable research institution")
                return 85, "Tier 2 (High)", reasons

        for domain, name in self.TIER_3_DOMAINS.items():
            if domain in url_lower:
                reasons.append(f"Tier 3 source: {name}")
                reasons.append("Reputable financial/economic journalism")
                return 70, "Tier 3 (Good)", reasons

        # Check for academic indicators
        if '.edu' in url_lower:
            reasons.append("Academic institution (.edu domain)")
            return 75, "Academic", reasons

        # Check for PDF (often indicates research papers)
        if '.pdf' in url_lower or 'paper' in title.lower():
            reasons.append("Research paper or academic publication")
            return 65, "Research Paper", reasons

        # Default for other sources
        reasons.append("General source - verify credibility independently")
        return 50, "General", reasons

    def rank_sources(self, sources: List[Dict]) -> List[Dict]:
        """Rank sources by credibility"""
        ranked = []

        for source in sources:
            url = source.get('url', '')
            title = source.get('title', '')
            description = source.get('description', '')

            score, tier, reasons = self.evaluate_source(url, title, description)

            ranked.append({
                'url': url,
                'title': title,
                'description': description,
                'credibility_score': score,
                'tier': tier,
                'reasons': reasons
            })

        # Sort by credibility score (highest first)
        ranked.sort(key=lambda x: x['credibility_score'], reverse=True)

        return ranked

    def display_results(self, ranked_sources: List[Dict]):
        """Display ranked sources in a readable format"""
        print("\n" + "=" * 80)
        print("RANKED CREDIBLE SOURCES")
        print("=" * 80)

        if not ranked_sources:
            print("\n⚠️  No sources found. Add search API integration to fetch results.")
            return

        for i, source in enumerate(ranked_sources, 1):
            print(f"\n{i}. {source['title']}")
            print(f"   URL: {source['url']}")
            print(f"   Credibility: {source['credibility_score']}/100 ({source['tier']})")
            print(f"   Reasons:")
            for reason in source['reasons']:
                print(f"   • {reason}")
            if source['description']:
                print(f"   Description: {source['description'][:150]}...")

    def get_recommended_sources(self, topic: str) -> Dict[str, List[str]]:
        """Get pre-curated list of recommended sources for common economic topics"""

        recommendations = {
            'tariffs': {
                'Tier 1 - Official/Research': [
                    'https://www.imf.org - Search IMF publications on trade policy',
                    'https://www.worldbank.org - World Bank trade reports',
                    'https://www.nber.org - NBER working papers on tariffs',
                    'https://www.wto.org - WTO tariff database and analysis',
                    'https://www.census.gov/foreign-trade - US trade statistics',
                ],
                'Tier 2 - Think Tanks/Academic': [
                    'https://www.piie.com - Peterson Institute trade policy briefs',
                    'https://www.brookings.edu - Brookings trade research',
                    'https://scholar.google.com - Academic papers on tariff effects',
                ],
                'Tier 3 - Quality Journalism': [
                    'https://www.economist.com - The Economist trade coverage',
                    'https://www.ft.com - Financial Times trade analysis',
                ]
            },
            'inflation': {
                'Tier 1 - Official/Research': [
                    'https://www.federalreserve.gov - Federal Reserve reports',
                    'https://www.bls.gov/cpi - Consumer Price Index data',
                    'https://www.imf.org - IMF inflation analysis',
                ],
                'Tier 2 - Think Tanks/Academic': [
                    'https://www.nber.org - NBER inflation research',
                    'https://www.brookings.edu - Brookings monetary policy',
                ],
            },
            'unemployment': {
                'Tier 1 - Official/Research': [
                    'https://www.bls.gov - Bureau of Labor Statistics',
                    'https://www.imf.org - IMF employment reports',
                    'https://www.oecd.org - OECD employment outlook',
                ],
            },
            'gdp': {
                'Tier 1 - Official/Research': [
                    'https://www.bea.gov - Bureau of Economic Analysis',
                    'https://www.worldbank.org - World Bank GDP data',
                    'https://www.imf.org - IMF economic outlook',
                ],
            },
        }

        topic_lower = topic.lower()

        # Find matching recommendations
        for key, sources in recommendations.items():
            if key in topic_lower or topic_lower in key:
                return sources

        # Return general recommendations if no match
        return {
            'General Economic Research': [
                'https://www.nber.org - National Bureau of Economic Research',
                'https://www.imf.org - International Monetary Fund',
                'https://www.worldbank.org - World Bank',
                'https://www.federalreserve.gov - Federal Reserve',
                'https://www.brookings.edu - Brookings Institution',
            ]
        }

    def generate_report(self, topic: str, output_file: str = None):
        """Generate a report of credible sources for a topic"""
        print(f"\n📊 CREDIBLE SOURCE REPORT: {topic.upper()}")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # Get recommended sources
        recommendations = self.get_recommended_sources(topic)

        print("\n📚 RECOMMENDED SOURCES BY CREDIBILITY TIER\n")

        for tier, sources in recommendations.items():
            print(f"\n{tier}:")
            print("-" * 60)
            for source in sources:
                print(f"  • {source}")

        print("\n\n💡 CREDIBILITY EVALUATION CRITERIA:")
        print("-" * 60)
        print("""
Tier 1 (Highest Credibility):
  • Official government statistical agencies
  • International organizations (IMF, World Bank, OECD)
  • Central banks and monetary authorities
  • Primary research institutions (NBER)

Tier 2 (High Credibility):
  • Peer-reviewed academic journals
  • University research centers
  • Reputable think tanks (Brookings, Peterson Institute)
  • Established research databases (JSTOR)

Tier 3 (Good Credibility):
  • Major financial news outlets (WSJ, FT, Bloomberg)
  • Specialized economic publications (The Economist)
  • Reuters and AP for factual reporting

Evaluation Tips:
  ✓ Check publication date (prefer recent for current topics)
  ✓ Look for citations and methodology
  ✓ Verify author credentials
  ✓ Cross-reference multiple sources
  ✓ Distinguish between data and opinion
        """)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(f"Credible Source Report: {topic}\n")
                f.write(f"Generated: {datetime.now()}\n\n")
                for tier, sources in recommendations.items():
                    f.write(f"\n{tier}:\n")
                    for source in sources:
                        f.write(f"  {source}\n")
            print(f"\n✅ Report saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Find credible sources for economic topics',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python source_finder_economics.py tariffs
  python source_finder_economics.py "trade policy" --output report.txt
  python source_finder_economics.py inflation
        """
    )

    parser.add_argument('topic', help='Economic topic to research (e.g., tariffs, inflation)')
    parser.add_argument('--output', '-o', help='Save report to file')

    args = parser.parse_args()

    finder = CredibleSourceFinder()
    finder.generate_report(args.topic, args.output)


if __name__ == "__main__":
    main()
