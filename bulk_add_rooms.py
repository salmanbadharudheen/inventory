import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.core.models import Organization
from apps.locations.models import Building, Floor, Room

def bulk_add_rooms():
    org = Organization.objects.get(name="TechCorp HQ")
    
    raw_data = """
 HALA BUILDING            1 Floor                101
 HALA BUILDING            1 Floor                102
 HALA BUILDING            1 Floor                105
 HALA BUILDING            1 Floor                106
 HALA BUILDING            1 Floor                107
 HALA BUILDING           10 Floor               1001
 HALA BUILDING           10 Floor               1003
 HALA BUILDING           10 Floor               1005
 HALA BUILDING         10th Floor               1002
 HALA BUILDING         10th Floor               1004
 HALA BUILDING         10th Floor               1005
 HALA BUILDING         10th Floor               1006
 HALA BUILDING         10th Floor               1007
 HALA BUILDING           11 Floor               1101
 HALA BUILDING           11 Floor               1103
 HALA BUILDING           11 Floor               1104
 HALA BUILDING           11 Floor               1106
 HALA BUILDING         11th Floor               1102
 HALA BUILDING         11th Floor               1105
 HALA BUILDING         11th Floor               1107
 HALA BUILDING           12 Floor               1201
 HALA BUILDING           12 Floor               1204
 HALA BUILDING           12 Floor               1206
 HALA BUILDING         12th Floor               1202
 HALA BUILDING         12th Floor               1203
 HALA BUILDING         12th Floor               1205
 HALA BUILDING         12th Floor               1207
 HALA BUILDING          1st Floor                103
 HALA BUILDING          1st Floor                104
 HALA BUILDING          1st Floor                107
 HALA BUILDING            2 Floor                201
 HALA BUILDING            2 Floor                202
 HALA BUILDING            2 Floor                205
 HALA BUILDING          2nd Floor                203
 HALA BUILDING          2nd Floor                204
 HALA BUILDING          2nd Floor                206
 HALA BUILDING          2nd Floor                207
 HALA BUILDING            3 Floor                301
 HALA BUILDING            3 Floor                302
 HALA BUILDING            3 Floor                303
 HALA BUILDING            3 Floor                306
 HALA BUILDING          3rd Floor                304
 HALA BUILDING          3rd Floor                305
 HALA BUILDING          3rd Floor                307
 HALA BUILDING            4 Floor                401
 HALA BUILDING            4 Floor                402
 HALA BUILDING            4 Floor                405
 HALA BUILDING          4th Floor                403
 HALA BUILDING          4th Floor                404
 HALA BUILDING          4th Floor                406
 HALA BUILDING          4th Floor                407
 HALA BUILDING            5 Floor                501
 HALA BUILDING            5 Floor                502
 HALA BUILDING            5 Floor                505
 HALA BUILDING          5th Floor                503
 HALA BUILDING          5th Floor                504
 HALA BUILDING          5th Floor                506
 HALA BUILDING          5th Floor                507
 HALA BUILDING            6 Floor                601
 HALA BUILDING            6 Floor                602
 HALA BUILDING            6 Floor                605
 HALA BUILDING          6th Floor                603
 HALA BUILDING          6th Floor                604
 HALA BUILDING          6th Floor                606
 HALA BUILDING          6th Floor                607
 HALA BUILDING            7 Floor                701
 HALA BUILDING            7 Floor                702
 HALA BUILDING            7 Floor                704
 HALA BUILDING            7 Floor                706
 HALA BUILDING          7th Floor                703
 HALA BUILDING          7th Floor                705
 HALA BUILDING          7th Floor                707
 HALA BUILDING            8 Floor                801
 HALA BUILDING            8 Floor                802
 HALA BUILDING            8 Floor                804
 HALA BUILDING          8th Floor                803
 HALA BUILDING          8th Floor                805
 HALA BUILDING          8th Floor                806
 HALA BUILDING          8th Floor                807
 HALA BUILDING            9 Floor                901
 HALA BUILDING            9 Floor                902
 HALA BUILDING            9 Floor                904
 HALA BUILDING          9th Floor                903
 HALA BUILDING          9th Floor                905
 HALA BUILDING          9th Floor                906
 HALA BUILDING          9th Floor                907
 HALA BUILDING            G Floor           Gym Area
 HALA BUILDING                 P5                 S1
 HALA BUILDING                 P5                S10
 HALA BUILDING                 P5                S11
 HALA BUILDING                 P5                 S3
 HALA BUILDING                 P5                 S5
 HALA BUILDING                 P5                 S6
 HALA BUILDING                 P5                 S8
 HALA BUILDING           P5 Floor                S12
 HALA BUILDING           P5 Floor                 S2
 HALA BUILDING           P5 Floor                 S4
 HALA BUILDING           P5 Floor                 S7
 HALA BUILDING           P5 Floor                 S9
HOTEL BUILDING          1st Floor                101
HOTEL BUILDING          1st Floor                102
HOTEL BUILDING          1st Floor                103
HOTEL BUILDING          1st Floor                104
HOTEL BUILDING          1st Floor                105
HOTEL BUILDING          1st Floor                106
HOTEL BUILDING          1st Floor                107
HOTEL BUILDING          1st Floor                108
HOTEL BUILDING          1st Floor                109
HOTEL BUILDING          1st Floor                110
HOTEL BUILDING          1st Floor                111
HOTEL BUILDING          1st Floor                112
HOTEL BUILDING          1st Floor                114
HOTEL BUILDING          1st Floor                115
HOTEL BUILDING          1st Floor                116
HOTEL BUILDING          1st Floor                117
HOTEL BUILDING          1st Floor                118
HOTEL BUILDING          1st Floor                119
HOTEL BUILDING          1st Floor                120
HOTEL BUILDING          1st Floor                121
HOTEL BUILDING          1st Floor                122
HOTEL BUILDING          1st Floor                123
HOTEL BUILDING          1st Floor                124
HOTEL BUILDING          1st Floor                125
HOTEL BUILDING          1st Floor        Server Room
HOTEL BUILDING          2nd Floor                201
HOTEL BUILDING          2nd Floor                202
HOTEL BUILDING          2nd Floor                203
HOTEL BUILDING          2nd Floor                204
HOTEL BUILDING          2nd Floor                205
HOTEL BUILDING          2nd Floor                206
HOTEL BUILDING          2nd Floor                207
HOTEL BUILDING          2nd Floor                208
HOTEL BUILDING          2nd Floor                209
HOTEL BUILDING          2nd Floor                210
HOTEL BUILDING          2nd Floor                211
HOTEL BUILDING          2nd Floor                212
HOTEL BUILDING          2nd Floor                214
HOTEL BUILDING          2nd Floor                215
HOTEL BUILDING          2nd Floor                216
HOTEL BUILDING          2nd Floor                217
HOTEL BUILDING          2nd Floor                218
HOTEL BUILDING          2nd Floor                219
HOTEL BUILDING          2nd Floor                220
HOTEL BUILDING          2nd Floor                221
HOTEL BUILDING          2nd Floor                222
HOTEL BUILDING          2nd Floor                223
HOTEL BUILDING          2nd Floor                224
HOTEL BUILDING          2nd Floor                225
HOTEL BUILDING          2nd Floor        Server Room
HOTEL BUILDING          3rd Floor                301
HOTEL BUILDING          3rd Floor                302
HOTEL BUILDING          3rd Floor                303
HOTEL BUILDING          3rd Floor                304
HOTEL BUILDING          3rd Floor                305
HOTEL BUILDING          3rd Floor                306
HOTEL BUILDING          3rd Floor                307
HOTEL BUILDING          3rd Floor                308
HOTEL BUILDING          3rd Floor                309
HOTEL BUILDING          3rd Floor                310
HOTEL BUILDING          3rd Floor                311
HOTEL BUILDING          3rd Floor                312
HOTEL BUILDING          3rd Floor                314
HOTEL BUILDING          3rd Floor                315
HOTEL BUILDING          3rd Floor                316
HOTEL BUILDING          3rd Floor                317
HOTEL BUILDING          3rd Floor                318
HOTEL BUILDING          3rd Floor                319
HOTEL BUILDING          3rd Floor                320
HOTEL BUILDING          3rd Floor                321
HOTEL BUILDING          3rd Floor                322
HOTEL BUILDING          3rd Floor                323
HOTEL BUILDING          3rd Floor                324
HOTEL BUILDING          3rd Floor                325
HOTEL BUILDING          3rd Floor        Server Room
HOTEL BUILDING          4th Floor                401
HOTEL BUILDING          4th Floor                402
HOTEL BUILDING          4th Floor                403
HOTEL BUILDING          4th Floor                404
HOTEL BUILDING          4th Floor                405
HOTEL BUILDING          4th Floor                406
HOTEL BUILDING          4th Floor                407
HOTEL BUILDING          4th Floor                408
HOTEL BUILDING          4th Floor                409
HOTEL BUILDING          4th Floor                410
HOTEL BUILDING          4th Floor                411
HOTEL BUILDING          4th Floor                412
HOTEL BUILDING          4th Floor                414
HOTEL BUILDING          4th Floor                415
HOTEL BUILDING          4th Floor                416
HOTEL BUILDING          4th Floor                417
HOTEL BUILDING          4th Floor                418
HOTEL BUILDING          4th Floor                419
HOTEL BUILDING          4th Floor                420
HOTEL BUILDING          4th Floor                421
HOTEL BUILDING          4th Floor                422
HOTEL BUILDING          4th Floor                423
HOTEL BUILDING          4th Floor                424
HOTEL BUILDING          4th Floor                425
HOTEL BUILDING          4th Floor        Server Room
HOTEL BUILDING          5th Floor                501
HOTEL BUILDING          5th Floor                502
HOTEL BUILDING          5th Floor                503
HOTEL BUILDING          5th Floor                504
HOTEL BUILDING          5th Floor                505
HOTEL BUILDING          5th Floor                506
HOTEL BUILDING          5th Floor                507
HOTEL BUILDING          5th Floor                508
HOTEL BUILDING          5th Floor                509
HOTEL BUILDING          5th Floor                510
HOTEL BUILDING          5th Floor                511
HOTEL BUILDING          5th Floor                512
HOTEL BUILDING          5th Floor                514
HOTEL BUILDING          5th Floor                515
HOTEL BUILDING          5th Floor                516
HOTEL BUILDING          5th Floor                517
HOTEL BUILDING          5th Floor                518
HOTEL BUILDING          5th Floor                519
HOTEL BUILDING          5th Floor                520
HOTEL BUILDING          5th Floor                521
HOTEL BUILDING          5th Floor                522
HOTEL BUILDING          5th Floor                523
HOTEL BUILDING          5th Floor                524
HOTEL BUILDING          5th Floor                525
HOTEL BUILDING          5th Floor        Server Room
HOTEL BUILDING          6th Floor                601
HOTEL BUILDING          6th Floor                602
HOTEL BUILDING          6th Floor                603
HOTEL BUILDING          6th Floor                604
HOTEL BUILDING          6th Floor                605
HOTEL BUILDING          6th Floor                606
HOTEL BUILDING          6th Floor                607
HOTEL BUILDING          6th Floor                608
HOTEL BUILDING          6th Floor                609
HOTEL BUILDING          6th Floor                610
HOTEL BUILDING          6th Floor                611
HOTEL BUILDING          6th Floor                612
HOTEL BUILDING          6th Floor                614
HOTEL BUILDING          6th Floor                615
HOTEL BUILDING          6th Floor                616
HOTEL BUILDING          6th Floor                617
HOTEL BUILDING          6th Floor                618
HOTEL BUILDING          6th Floor                619
HOTEL BUILDING          6th Floor                620
HOTEL BUILDING          6th Floor                621
HOTEL BUILDING          6th Floor                622
HOTEL BUILDING          6th Floor                623
HOTEL BUILDING          6th Floor                624
HOTEL BUILDING          6th Floor                625
HOTEL BUILDING          6th Floor        Server Room
HOTEL BUILDING          7th Floor                701
HOTEL BUILDING          7th Floor                702
HOTEL BUILDING          7th Floor                703
HOTEL BUILDING          7th Floor                704
HOTEL BUILDING          7th Floor                705
HOTEL BUILDING          7th Floor                706
HOTEL BUILDING          7th Floor                707
HOTEL BUILDING          7th Floor                708
HOTEL BUILDING          7th Floor                709
HOTEL BUILDING          7th Floor                710
HOTEL BUILDING          7th Floor                711
HOTEL BUILDING          7th Floor                712
HOTEL BUILDING          7th Floor                714
HOTEL BUILDING          7th Floor                715
HOTEL BUILDING          7th Floor                716
HOTEL BUILDING          7th Floor                717
HOTEL BUILDING          7th Floor                718
HOTEL BUILDING          7th Floor                719
HOTEL BUILDING          7th Floor                720
HOTEL BUILDING          7th Floor                721
HOTEL BUILDING          7th Floor                722
HOTEL BUILDING          7th Floor                723
HOTEL BUILDING          7th Floor                724
HOTEL BUILDING          7th Floor                725
HOTEL BUILDING          7th Floor        Server Room
HOTEL BUILDING          8th Floor                801
HOTEL BUILDING          8th Floor                802
HOTEL BUILDING          8th Floor                803
HOTEL BUILDING          8th Floor                804
HOTEL BUILDING          8th Floor                805
HOTEL BUILDING          8th Floor                806
HOTEL BUILDING          8th Floor                807
HOTEL BUILDING          8th Floor                808
HOTEL BUILDING          8th Floor                809
HOTEL BUILDING          8th Floor                810
HOTEL BUILDING          8th Floor                811
HOTEL BUILDING          8th Floor                812
HOTEL BUILDING          8th Floor                814
HOTEL BUILDING          8th Floor                815
HOTEL BUILDING          8th Floor                816
HOTEL BUILDING          8th Floor                817
HOTEL BUILDING          8th Floor                818
HOTEL BUILDING          8th Floor                819
HOTEL BUILDING          8th Floor                820
HOTEL BUILDING          8th Floor                821
HOTEL BUILDING          8th Floor        Server Room
HOTEL BUILDING          9th Floor                901
HOTEL BUILDING          9th Floor                902
HOTEL BUILDING          9th Floor                903
HOTEL BUILDING          9th Floor                904
HOTEL BUILDING          9th Floor                905
HOTEL BUILDING          9th Floor                906
HOTEL BUILDING          9th Floor                907
HOTEL BUILDING          9th Floor                908
HOTEL BUILDING          9th Floor                909
HOTEL BUILDING          9th Floor                910
HOTEL BUILDING          9th Floor                911
HOTEL BUILDING          9th Floor                912
HOTEL BUILDING          9th Floor                914
HOTEL BUILDING          9th Floor                915
HOTEL BUILDING          9th Floor                917
HOTEL BUILDING          9th Floor                919
HOTEL BUILDING          9th Floor                920
HOTEL BUILDING          9th Floor        Server Room
HOTEL BUILDING           B1 Floor        Server Room
HOTEL BUILDING            Banquet            Banquet
HOTEL BUILDING Housekeeping Store Housekeeping Store
HOTEL BUILDING           LG Floor            Finance
HOTEL BUILDING           LG Floor        Server Room
HOTEL BUILDING            M Floor        Server Room
HOTEL BUILDING            S Floor        Server Room
HOTEL BUILDING         STORE ROOM         STORE ROOM
HOTEL BUILDING           UG Floor        Server Room
    """

    lines = [l.strip() for l in raw_data.split('\n') if l.strip()]
    
    # Skip header if present
    if lines and "BUILDING" in lines[0] and "ROOM_NO" in lines[0]:
        lines = lines[1:]

    created_count = 0
    skipped_count = 0
    error_count = 0

    for line in lines:
        # User format: BUILDING (multiple spaces) FLOOR (multiple spaces) ROOM_NO
        # Using a more robust split for aligned text
        parts = re.split(r'\s{2,}', line)
        
        if len(parts) >= 3:
            building_name = parts[0].strip().title()
            floor_name = parts[1].strip().title()
            room_name = parts[2].strip() # Keep room numbers as provided (usually digits)
        else:
            # Fallback for weird lines
            print(f"Skipping malformed line: {line}")
            error_count += 1
            continue

        try:
            # 1. Get Building
            building = Building.objects.get(name=building_name)
            
            # 2. Get or Create Floor (ensuring it exists under this building)
            floor, _ = Floor.objects.get_or_create(
                organization=org,
                building=building,
                name=floor_name
            )
            
            # 3. Get or Create Room
            room, created = Room.objects.get_or_create(
                organization=org,
                floor=floor,
                name=room_name
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

    print(f"Successfully added {created_count} rooms.")
    print(f"Skipped {skipped_count} existing rooms.")
    print(f"Errors: {error_count}")

if __name__ == '__main__':
    bulk_add_rooms()
