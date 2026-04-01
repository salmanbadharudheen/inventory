"""
Script to populate company codes for existing companies
Run this once to ensure all existing companies have auto-generated codes
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.assets.models import Company

def populate_company_codes():
    print("=" * 70)
    print("POPULATE COMPANY CODES")
    print("=" * 70)
    print()
    
    # Find companies without codes
    companies_without_codes = Company.objects.filter(code='')
    total_companies = Company.objects.count()
    
    print(f"Total companies in system: {total_companies}")
    print(f"Companies without codes: {companies_without_codes.count()}")
    print()
    
    if companies_without_codes.count() == 0:
        print("✓ All companies already have codes!")
        print()
        return
    
    print("Generating codes for companies...")
    print("-" * 70)
    
    updated_count = 0
    for company in companies_without_codes:
        old_code = company.code
        
        # Trigger auto-generation by saving
        company.code = ''
        company.save()
        
        print(f"  {company.name:30} → {company.code}")
        updated_count += 1
    
    print()
    print("=" * 70)
    print(f"✓ Successfully generated codes for {updated_count} companies!")
    print("=" * 70)
    print()
    
    # Show all companies with their codes
    print("ALL COMPANIES WITH CODES:")
    print("-" * 70)
    all_companies = Company.objects.all().order_by('organization', 'name')
    
    current_org = None
    for company in all_companies:
        if current_org != company.organization:
            current_org = company.organization
            print(f"\n[{company.organization.name}]")
        print(f"  {company.code:3} - {company.name}")
    
    print()

if __name__ == '__main__':
    populate_company_codes()
