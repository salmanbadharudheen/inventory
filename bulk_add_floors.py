import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.core.models import Organization
from apps.locations.models import Building, Floor

def bulk_add_floors():
    org = Organization.objects.get(name="TechCorp HQ")
    
    raw_data = """
0	HALA BUILDING	1 Floor
1	HALA BUILDING	10 Floor
2	HALA BUILDING	10th Floor
3	HALA BUILDING	11 Floor
4	HALA BUILDING	11th Floor
5	HALA BUILDING	12 Floor
6	HALA BUILDING	12th Floor
7	HALA BUILDING	1st Floor
8	HALA BUILDING	2 Floor
9	HALA BUILDING	2nd Floor
10	HALA BUILDING	3 Floor
11	HALA BUILDING	3P
12	HALA BUILDING	3rd Floor
13	HALA BUILDING	4 Floor
14	HALA BUILDING	4P Floor
15	HALA BUILDING	4th Floor
16	HALA BUILDING	5 Floor
17	HALA BUILDING	5th Floor
18	HALA BUILDING	6 Floor
19	HALA BUILDING	6th Floor
20	HALA BUILDING	7 Floor
21	HALA BUILDING	7th Floor
22	HALA BUILDING	8 Floor
23	HALA BUILDING	8th Floor
24	HALA BUILDING	9 Floor
25	HALA BUILDING	9th Floor
26	HALA BUILDING	G Floor
27	HALA BUILDING	GROUND FLOOR
28	HALA BUILDING	Ground Floor
29	HALA BUILDING	P5
30	HALA BUILDING	P5 Floor
31	HOTEL BUILDING	1st Floor
32	HOTEL BUILDING	2nd Floor
33	HOTEL BUILDING	3rd Floor
34	HOTEL BUILDING	4th Floor
35	HOTEL BUILDING	5th Floor
36	HOTEL BUILDING	6th Floor
37	HOTEL BUILDING	7th Floor
38	HOTEL BUILDING	8th Floor
39	HOTEL BUILDING	9th Floor
40	HOTEL BUILDING	B1
41	HOTEL BUILDING	B1 Floor
42	HOTEL BUILDING	Banquet
43	HOTEL BUILDING	Beach
44	HOTEL BUILDING	ENTRANCE
45	HOTEL BUILDING	Housekeeping Store
46	HOTEL BUILDING	LG FLOOR
47	HOTEL BUILDING	LG Floor
48	HOTEL BUILDING	M FLOOR
49	HOTEL BUILDING	M Floor
50	HOTEL BUILDING	PH Floor
51	HOTEL BUILDING	PH1
52	HOTEL BUILDING	PH1 Floor
53	HOTEL BUILDING	S Floor
54	HOTEL BUILDING	SPA Floor
55	HOTEL BUILDING	STORE ROOM
56	HOTEL BUILDING	UG Floor
    """

    lines = [l.strip() for l in raw_data.split('\n') if l.strip()]
    
    created_count = 0
    skipped_count = 0
    error_count = 0

    for line in lines:
        # Split by tab or multiple spaces
        parts = re.split(r'\t|\s{2,}', line)
        
        # Format: index, building_name, floor_name
        # Note: If splitting by multiple spaces, the index count might vary if it's not a tab.
        # Let's try to be smart.
        if len(parts) >= 3:
            building_name = parts[1].strip().title()
            floor_name = parts[2].strip().title()
        elif len(parts) == 2:
            # Maybe the index is missing? Or space-separated.
            # "HALA BUILDING" is two words.
            # Let's re-split more carefully if it fails.
            # The provided data looks like: index <space> BUILDING_NAME <tab/multiple spaces> FLOOR_NAME
            # Actually, looks like tab or aligned spaces.
            building_name = parts[0].strip().title()
            floor_name = parts[1].strip().title()
            # Remove index if it's there
            if building_name.replace('.','').isdigit():
                 # This wasn't building_name, it was index.
                 # This case shouldn't happen with split >= 3.
                 pass

        # Clean building_name from leading digits if they leaked
        building_name = re.sub(r'^\d+\s+', '', building_name)

        try:
            building = Building.objects.get(name=building_name)
            floor, created = Floor.objects.get_or_create(
                organization=org,
                building=building,
                name=floor_name
            )
            if created:
                created_count += 1
            else:
                skipped_count += 1
        except Building.DoesNotExist:
            print(f"Error: Building '{building_name}' not found.")
            error_count += 1
        except Exception as e:
            print(f"Error processing line '{line}': {e}")
            error_count += 1

    print(f"Successfully added {created_count} floors.")
    print(f"Skipped {skipped_count} existing floors.")
    print(f"Errors: {error_count}")

if __name__ == '__main__':
    bulk_add_floors()
