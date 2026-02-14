import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.core.models import Organization
from apps.locations.models import Location, SubLocation

def bulk_add_sublocations():
    org = Organization.objects.get(name="TechCorp HQ")
    
    raw_data = """
                 LOCATION                    SUB_LOCATION
                     AHU BALL ROOM                              NA
 AIR HANDLING PLANT ROOM LEFT SIDE                              NA
AIR HANDLING PLANT ROOM RIGHT SIDE                              NA
                  Associate Lounge                Associate Lounge
                          B1 Floor                    Service Lift
            BAB AL BAHR RESTAURANT                         KITCHEN
            BAB AL BAHR RESTAURANT                    OUTSIDE AREA
            BAB AL BAHR RESTAURANT                     SHISHA ROOM
            BAB AL BAHR RESTAURANT                      STORE ROOM
            BAB AL BAHR RESTAURANT                      UPPER AREA
                       BACK OFFICE             SAFETY DEPOSIT ROOM
                  BANQUET CORRIDOR                              NA
                      BATTERY ROOM                              NA
                        BEACH AREA                      BEACH AREA
                 Ball Room Storage               Ball Room Storage
                    Ballroom Store                  Ballroom Store
                           Banquet                         Banquet
                           Banquet                    Banquet Hall
                           Banquet         Banquet Hall - Backside
                           Banquet         Banquet Hall - VIP Room
                           Banquet                        Corridor
                           Banquet                        Washroom
                   Banquet Storage                 Banquet Storage
                          Basement                        MEP Room
                          Basement                         Parking
                  Basement Parking                Basement Parking
                             Beach                           Beach
                         CCTV Room                       CCTV Room
                       CLINIC ROOM                           WF 12
                     COOLING TOWER                 ELECTRICAL ROOM
                     COOLING TOWER                              NA
                          Corridor                        Corridor
                          Corridor           Employee Smoking Zone
                          Corridor                M Floor Corridor
                           Du Room                        Corridor
                   ELECTRICAL ROOM             BACK SIDE DRY STORE
 ELECTRICAL ROOM - BUSINESS CENTER                              NA
              ELECTRICAL ROOM - SL                              NA
           ELECTRICAL ROOM - VISTA                              NA
                 ELECTRICAL ROOM 1                              NA
                ENGINEERING OFFICE    DIRECTOR OF ENGINEERING ROOM
                ENGINEERING OFFICE               ENGINEERING STORE
              ENGINEERING WORKSHOP                        BMS ROOM
              ENGINEERING WORKSHOP             ELECTRICAL WORKSHOP
               Employees Cafeteria             Employees Cafeteria
                Engineering Office                 Director Office
                 Engineering Store               Engineering Store
                        F&B Office                      F&B Office
                        F&B Office                         Storage
             FINANCE DIRECTOR ROOM                    FINANCE ROOM
                    FINANCE OFFICE                   COUNTING ROOM
                    FINANCE OFFICE       PURCHASING MANAGER OFFICE
                    FINANCE OFFICE                 SECURITY OFFICE
                           Finance                         Finance
                      Front Office                    Front Office
                  GENERAL WORKSHOP                GENERAL WORKSHOP
                         GM Office          Director of Operations
                         GM Office                       File Room
                         GM Office                       GM Office
                         GM Office                    Meeting Room
                        Guest Room              Al Dana Creek View
                        Guest Room                 Al Dana Seaview
                        Guest Room                     Amiri Suite
                        Guest Room               Deluxe Creek King
                        Guest Room               Deluxe Creek Twin
                        Guest Room             Deluxe Seaview King
                        Guest Room             Deluxe Seaview Twin
                        Guest Room                     Royal Suite
               Guest Room Corridor                        Corridor
               Guest Room Corridor Corridor Opposite to Guest Lift
               Guest Room Corridor             Guest Room Corridor
               Guest Room Corridor              Housekeeping Store
               Guest Room Corridor                 LIFT LOBBY AREA
                    HOUSING OFFICE                   HALA BUILDING
                         HR OFFICE                      FURN STORE
                         HR OFFICE                HR DIRECTOR ROOM
                         HR OFFICE           TRAINING MANAGER ROOM
                         HR OFFICE                   TRAINING ROOM
                         HVAC Room                       HVAC Room
                Housekeeping Store              Housekeeping Store
                 IT Manager Office               IT Manager Office
                         IT Office                       IT Office
                         IT Office                         Storage
                    IT Server Room                         Storage
                    Kids Play Area                  Kids Play Area
                           Kitchen                    Cold Kitchen
                           Kitchen    Cold Kitchen - Blast Chiller
                           Kitchen     Cold Kitchen - Chiller S#12
                           Kitchen     Flower Preparation Corridor
                           Kitchen                    Freezer Room
                           Kitchen                         Kitchen
                           Kitchen              Kitchen Food Store
                           Kitchen                   Kitchen Store
                           Kitchen                    Main Kitchen
                           Kitchen                  Pastry Kitchen
                           Kitchen   Pastry Kitchen - Chiller S#14
                           Kitchen    Pastry Kitchen - Freezer S#5
                           Kitchen               Pasty Chef office
                           Kitchen                 Poultry Kitchen
                           Kitchen                    Safi Kitchen
                      LAUNDRY ROOM              CLEANED LINEN ROOM
                      LAUNDRY ROOM            LAUNDRY MANAGER ROOM
                          LG FLOOR                       CCTV Room
                          LG FLOOR              CCTV Room Corridor
                          LG FLOOR                  IT Server Room
                          LG FLOOR                    Loading Area
                          LG FLOOR                 Security Office
                          LG FLOOR              Visitorss Entrance
                          LG Floor                        Corridor
                        LOBBY AREA            BESIDE TRAINING ROOM
                        LOBBY AREA         BESIDE VISTA RESTAURANT
                      Laguage Room                    Laguage Room
                          Laundery                        Laundery
                             Lobby                       Concierge
                             Lobby       Concierge Business Centre
                             Lobby                        Corridor
                             Lobby           Escape Equestrian Bar
                             Lobby                           Lobby
                             Lobby                 Lobby Reception
                             Lobby                        Washroom
                 M FLOOR SL3 LOBBY                              NA
                MEJHANA RESTAURANT                      STORE ROOM
               MEP ELECTRICAL ROOM                              NA
                    Main Entrancce                   Security Room
                     Main Entrance                  Main Entrancce
                     Main Entrance                    Mejhana Side
                      Main Kitchen                    Main Kitchen
                      Main Kitchen           Main Kitchen Corridor
                      Main Kitchen           Main Kitchen Office 2
                      Main Kitchen                  Pastry Kitchen
                      Main Kitchen                   Pastry office
                           Majhana              Majhana Store Room
                            Majlis                        Corridor
                            Majlis               Junior Board Room
                            Majlis                         Kitchen
                            Majlis                        Majlis 1
                            Majlis                        Majlis 2
                            Majlis                    Majlis 3 & 4
                            Majlis                    Majlis Store
                  Marketing Office                Marketing Office
                           Mejhana                         Kitchen
                           Mejhana                         Mejhana
                           Mejhana                Mejhana Entrance
                           Mejhana            Mejhana Smoking Area
                           Mejhana                 Mejhana Storage
                           Mejhana                Solid Linen Room
                           Mejhana                         Storage
                      PARKING AREA                   HALA BUILDING
                               PH1                             PH1
                        PLANT ROOM      COLD WATER IRRIGATION ROOM
                        PLANT ROOM                  FIRE PUMP ROOM
                        PLANT ROOM        STB WATER TREATMENT ROOM
                        PLANT ROOM                            WF 1
            POOL EQUIPMENT STORAGE                              NA
                    PROJECTOR ROOM                              NA
                            Pantry                          Pantry
                           Parking                         Storage
                    RECEPTION AREA                   HALA BUILDING
                         Ramp Room                       Ramp Room
                    Receiving Area                  Receiving Area
                           Rooftop                         Rooftop
                      Rooftop Exit                    Rooftop Exit
               S&M MANAGERS OFFICE                      STORE ROOM
                SPA Floor Backside               Service Staircase
                          SPA ROOM                         BALCONY
                          SPA ROOM                 ELECTRICAL ROOM
          STAFF ACCOMMODATION ROOM                   HALA BUILDING
STAFF ACCOMMODATION ROOM - STORAGE                   HALA BUILDING
                  STATIONERY STORE       FINANCE STORE(NEXT TO HR)
                             STORE                   HALA BUILDING
                        STORE ROOM                      STORE ROOM
                   Safi Restaurant                 Safi Restaurant
                     Security Room                        Corridor
                       Server Room                     Server Room
                       Server Room                         Storage
                    Spa plant room                  Spa plant room
               Stevwariding Office             Stevwariding Office
                      Storage Room                    Storage Room
                       TIME OFFICE               ( receiving area)
                  TIME OFFICE room               ( receiving area)
                  VISTA RESTAURANT                    OUTSIDE AREA
                  VISTA RESTAURANT               VISTA BAR COUNTER
                             Vista                         Kitchen
                     WATCHMAN ROOM                   HALA BUILDING
    """

    lines = [l.strip() for l in raw_data.split('\n') if l.strip()]
    
    # Skip header
    if lines and "LOCATION" in lines[0]:
        lines = lines[1:]

    created_count = 0
    skipped_count = 0
    error_count = 0

    for line in lines:
        # Split by 2 or more spaces
        parts = re.split(r'\s{2,}', line)
        if len(parts) >= 2:
            location_name = parts[0].strip().title()
            sub_location_name = parts[1].strip().title()
            
            if sub_location_name == "Na" or not sub_location_name:
                continue

            # Find matching location(s)
            locations = Location.objects.filter(name=location_name)
            
            if not locations.exists():
                print(f"Error: Location '{location_name}' not found for sub-location '{sub_location_name}'.")
                error_count += 1
                continue

            # If there are multiple locations with the same name, we'll add the sub-location to all of them
            # or should we be more specific? The user provided the LOCATION name only.
            # Given the previous context, these locations belong to specific buildings.
            # I will add the sub-location to all matching locations to be safe,
            # but usually it's better to be specific.
            # However, the user data doesn't provide Site/Building here.
            
            for loc in locations:
                sub_loc, created = SubLocation.objects.get_or_create(
                    organization=org,
                    location=loc,
                    name=sub_location_name
                )
                if created:
                    created_count += 1
                else:
                    skipped_count += 1
        else:
            print(f"Skipping malformed line: {line}")

    print(f"Successfully added {created_count} sub-locations.")
    print(f"Skipped {skipped_count} existing sub-locations.")
    print(f"Errors: {error_count}")

if __name__ == '__main__':
    bulk_add_sublocations()
