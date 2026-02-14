import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.core.models import Organization
from apps.locations.models import Region, Site, Building, Location, Branch

def bulk_add_locations():
    org = Organization.objects.get(name="TechCorp HQ")
    
    # Ensure Parent Objects
    region, _ = Region.objects.get_or_create(
        organization=org,
        name="Northern Emirates",
        defaults={'code': 'NE'}
    )
    
    branch, _ = Branch.objects.get_or_create(
        organization=org,
        code="MAIN",
        defaults={'name': 'Main Branch'}
    )
    
    raw_data = """
 SITE       BUILDING                                                LOCATION
AJMAN  HALA BUILDING                                          HOUSING OFFICE
AJMAN  HALA BUILDING                                            PARKING AREA
AJMAN  HALA BUILDING                                          RECEPTION AREA
AJMAN  HALA BUILDING                                STAFF ACCOMMODATION ROOM
AJMAN  HALA BUILDING                      STAFF ACCOMMODATION ROOM - STORAGE
AJMAN  HALA BUILDING                                                   STORE
AJMAN  HALA BUILDING                                           WATCHMAN ROOM
AJMAN HOTEL BUILDING                                           AHU BALL ROOM
AJMAN HOTEL BUILDING                                          AHU PLANT ROOM
AJMAN HOTEL BUILDING                       AIR HANDLING PLANT ROOM LEFT SIDE
AJMAN HOTEL BUILDING                      AIR HANDLING PLANT ROOM RIGHT SIDE
AJMAN HOTEL BUILDING                                  AL SHORFA CASH COUNTER
AJMAN HOTEL BUILDING                                  AL SHORFA GENERAL VIEW
AJMAN HOTEL BUILDING                                  AL SHORFA SITTING AREA
AJMAN HOTEL BUILDING                                           ALCOHOL STORE
AJMAN HOTEL BUILDING                                        Associate Lounge
AJMAN HOTEL BUILDING                                                B1 Floor
AJMAN HOTEL BUILDING                                              B1 PARKING
AJMAN HOTEL BUILDING                                  BAB AL BAHR RESTAURANT
AJMAN HOTEL BUILDING                          BAB AL BAHR RESTAURANT OUTSIDE
AJMAN HOTEL BUILDING                                      BAB CASH COUNTER 1
AJMAN HOTEL BUILDING                                      BAB CASH COUNTER 2
AJMAN HOTEL BUILDING                                        BAB CHILLER ROOM
AJMAN HOTEL BUILDING                                             BAB DJ AREA
AJMAN HOTEL BUILDING                                        BAB GENERAL VIEW
AJMAN HOTEL BUILDING                                      BAB GENERAL VIEW 2
AJMAN HOTEL BUILDING                                  BAB INSIDE NEAR TOILET
AJMAN HOTEL BUILDING                                             BAB KITCHEN
AJMAN HOTEL BUILDING                                            BAB ROOF TOP
AJMAN HOTEL BUILDING                                         BAB SHISHA AREA
AJMAN HOTEL BUILDING                                        BAB SITTING AREA
AJMAN HOTEL BUILDING                                  BAB SLIDING DOOR ENTRY
AJMAN HOTEL BUILDING                                             BAB TERRACE
AJMAN HOTEL BUILDING                                     BAB TERRACE COUNTER
AJMAN HOTEL BUILDING                              BAB TOP SERVICE LIFT LOBBY
AJMAN HOTEL BUILDING                                  BAB WASHROOM CORRIDORE
AJMAN HOTEL BUILDING                                             BACK OFFICE
AJMAN HOTEL BUILDING                                      BACK OFFICE PANTRY
AJMAN HOTEL BUILDING                                              BALLROOM A
AJMAN HOTEL BUILDING                                              BALLROOM B
AJMAN HOTEL BUILDING                                      BALLROOM BACK AREA
AJMAN HOTEL BUILDING                                              BALLROOM C
AJMAN HOTEL BUILDING                          BALLROOM CORRIDORE NEAR TOILET
AJMAN HOTEL BUILDING                                 BANQUET CAPTAIN MANAGER
AJMAN HOTEL BUILDING                                        BANQUET CORRIDOR
AJMAN HOTEL BUILDING                              BASEMENT EXIT BARRIER RAMP
AJMAN HOTEL BUILDING                                      BASEMENT EXIT RAMP
AJMAN HOTEL BUILDING                                    BASEMENT STAIRCASE 5
AJMAN HOTEL BUILDING                                            BATTERY ROOM
AJMAN HOTEL BUILDING                                              BEACH AREA
AJMAN HOTEL BUILDING                               BEACH ENTRANCE FROM HOTEL
AJMAN HOTEL BUILDING                                              BEACH VIEW
AJMAN HOTEL BUILDING                                             BOILER ROOM
AJMAN HOTEL BUILDING                                           BREAKOUT AREA
AJMAN HOTEL BUILDING                                           BUILDING VIEW
AJMAN HOTEL BUILDING                                         BUILDING VIEW 2
AJMAN HOTEL BUILDING                                       Ball Room Storage
AJMAN HOTEL BUILDING                                          Ballroom Store
AJMAN HOTEL BUILDING                                                 Banquet
AJMAN HOTEL BUILDING                                         Banquet Storage
AJMAN HOTEL BUILDING                                                Basement
AJMAN HOTEL BUILDING                                        Basement Parking
AJMAN HOTEL BUILDING                                                   Beach
AJMAN HOTEL BUILDING                                     CAFETERIA CORRIDORE
AJMAN HOTEL BUILDING                                         CALORIFIER ROOM
AJMAN HOTEL BUILDING                                            CAR ENTRANCE
AJMAN HOTEL BUILDING                                    CAR ENTRANCE BARRIER
AJMAN HOTEL BUILDING                                       CAR ENTRANCE RAMP
AJMAN HOTEL BUILDING                                 CASH DROP INSIDE CLINIC
AJMAN HOTEL BUILDING                                          CASH DROP ROOM
AJMAN HOTEL BUILDING                                               CCTV ROOM
AJMAN HOTEL BUILDING                                               CCTV Room
AJMAN HOTEL BUILDING                                               CCTV room
AJMAN HOTEL BUILDING                                    CENTRAL BATTERY ROOM
AJMAN HOTEL BUILDING                                            CHILLER ROOM
AJMAN HOTEL BUILDING                                             CLINIC ROOM
AJMAN HOTEL BUILDING                              COLD WATER IRRIGATION ROOM
AJMAN HOTEL BUILDING                                          COMRESSOR ROOM
AJMAN HOTEL BUILDING                                               CONCIERGE
AJMAN HOTEL BUILDING                                          CONCIERGE DESK
AJMAN HOTEL BUILDING                                           COOLING TOWER
AJMAN HOTEL BUILDING                                CORRIDOR NEAR MAJLIS-1&2
AJMAN HOTEL BUILDING                                  CORRIDOR NEAR MAJLIS-4
AJMAN HOTEL BUILDING                                CORRIDOR NEAR MARKETTING
AJMAN HOTEL BUILDING                                               CORRIDORE
AJMAN HOTEL BUILDING                       CORRIDORE NEAR ENGINEERING OFFICE
AJMAN HOTEL BUILDING                                  CORRIDORE NEAR FINANCE
AJMAN HOTEL BUILDING                                CORRIDORE NEAR HR OFFICE
AJMAN HOTEL BUILDING                                 CORRIDORE NEAR SL LOBBY
AJMAN HOTEL BUILDING                                                Corridor
AJMAN HOTEL BUILDING                                DIESEL STORAGE TANK ROOM
AJMAN HOTEL BUILDING                                    DIRECTOR OF SECURITY
AJMAN HOTEL BUILDING                              DRIVE WAY NEAR DIESEL TANK
AJMAN HOTEL BUILDING                                    DRIVE WAY NEAR LOT 1
AJMAN HOTEL BUILDING                                   DRIVE WAY NEAR LOT 25
AJMAN HOTEL BUILDING                               DRIVEWAY NEAR STAIRCASE 2
AJMAN HOTEL BUILDING                                                 DU ROOM
AJMAN HOTEL BUILDING                                                 Du Room
AJMAN HOTEL BUILDING                                         ELECTRICAL ROOM
AJMAN HOTEL BUILDING                       ELECTRICAL ROOM - BUSINESS CENTER
AJMAN HOTEL BUILDING                                    ELECTRICAL ROOM - SL
AJMAN HOTEL BUILDING                                 ELECTRICAL ROOM - VISTA
AJMAN HOTEL BUILDING                                       ELECTRICAL ROOM 1
AJMAN HOTEL BUILDING                                      ENGINEEIRING STORE
AJMAN HOTEL BUILDING                                      ENGINEERING OFFICE
AJMAN HOTEL BUILDING                                    ENGINEERING WORKSHOP
AJMAN HOTEL BUILDING                                      ENTRANCE DRIVE WAY
AJMAN HOTEL BUILDING                                           ENTRANCE HALL
AJMAN HOTEL BUILDING                                 ESCAPE BAR CASH COUNTER
AJMAN HOTEL BUILDING                               ESCAPE BAR GENERAL VIEW 1
AJMAN HOTEL BUILDING                                           ETISALAT ROOM
AJMAN HOTEL BUILDING                                     EXECUTIVE BOARDROOM
AJMAN HOTEL BUILDING                            EXECUTIVE HOUSEKEEPER OFFICE
AJMAN HOTEL BUILDING                           EXIT DOOR NEAR CHEMICAL STORE
AJMAN HOTEL BUILDING                              EXIT DOOR NEAR FLOWER SHOP
AJMAN HOTEL BUILDING                                EXIT DOOR NEAR KIDS CLUB
AJMAN HOTEL BUILDING                             EXIT DOOR TO RECEIVING AREA
AJMAN HOTEL BUILDING                                    EXIT TO SMOKING AREA
AJMAN HOTEL BUILDING                                     Employees Cafeteria
AJMAN HOTEL BUILDING                                      Engineering Office
AJMAN HOTEL BUILDING                                       Engineering Store
AJMAN HOTEL BUILDING                                              F&B Office
AJMAN HOTEL BUILDING                                               F&B STORE
AJMAN HOTEL BUILDING                                      F&B STORE CORRIDOR
AJMAN HOTEL BUILDING                                   FINANCE DIRECTOR ROOM
AJMAN HOTEL BUILDING                                          FINANCE OFFICE
AJMAN HOTEL BUILDING                                           FINANCE STORE
AJMAN HOTEL BUILDING                                     FIRE COMMAND CENTER
AJMAN HOTEL BUILDING                                          FIRE PUMP ROOM
AJMAN HOTEL BUILDING                                               FOOD AREA
AJMAN HOTEL BUILDING                                 FRONT OFFICE ADMIN ROOM
AJMAN HOTEL BUILDING                                                 Finance
AJMAN HOTEL BUILDING                                            Front Office
AJMAN HOTEL BUILDING                                         GENERAL CASHIER
AJMAN HOTEL BUILDING                                   GENERAL CASHIER STORE
AJMAN HOTEL BUILDING                                  GENERAL CASHIER WINDOW
AJMAN HOTEL BUILDING                                        GENERAL WORKSHOP
AJMAN HOTEL BUILDING                                          GENERATOR ROOM
AJMAN HOTEL BUILDING                                               GM Office
AJMAN HOTEL BUILDING                                                GSM ROOM
AJMAN HOTEL BUILDING                                     GUARD ROOM ENTRANCE
AJMAN HOTEL BUILDING                                          GUEST ENTRANCE
AJMAN HOTEL BUILDING                                   GUEST LIFT 4 ENTRANCE
AJMAN HOTEL BUILDING                                     GUEST LIFT ENTRANCE
AJMAN HOTEL BUILDING                                        GUEST LIFT LOBBY
AJMAN HOTEL BUILDING                               GUEST LIFT LOBBY ENTRANCE
AJMAN HOTEL BUILDING                            GUEST LIFT LOBBY ENTRANCE B1
AJMAN HOTEL BUILDING                                         GUEST LIFT SIDE
AJMAN HOTEL BUILDING                                              GUEST ROOM
AJMAN HOTEL BUILDING                                                     GYM
AJMAN HOTEL BUILDING                                                GYM LIFT
AJMAN HOTEL BUILDING                                          GYM LIFT LOBBY
AJMAN HOTEL BUILDING                                              GYM OFFICE
AJMAN HOTEL BUILDING                                              GYM VIEW 1
AJMAN HOTEL BUILDING                                              GYM VIEW 2
AJMAN HOTEL BUILDING                                              GYM VIEW 3
AJMAN HOTEL BUILDING                                              Guest Room
AJMAN HOTEL BUILDING                                     Guest Room Corridor
AJMAN HOTEL BUILDING                            HIGH VOLTAGE ELECTRICAL ROOM
AJMAN HOTEL BUILDING                                       HOLDING TANK ROOM
AJMAN HOTEL BUILDING                               HOTEL ENTRANCE NEAR HORSE
AJMAN HOTEL BUILDING                                        HOTEL FRONT VIEW
AJMAN HOTEL BUILDING                                     HOUSEKEEPING OFFICE
AJMAN HOTEL BUILDING                                      HOUSEKEEPING STORE
AJMAN HOTEL BUILDING                                               HR OFFICE
AJMAN HOTEL BUILDING                                      Housekeeping Store
AJMAN HOTEL BUILDING                                          INSIDE LV ROOM
AJMAN HOTEL BUILDING                                        IRD CASH COUNTER
AJMAN HOTEL BUILDING                                         IT MANAGER ROOM
AJMAN HOTEL BUILDING                                       IT Manager Office
AJMAN HOTEL BUILDING                                               IT Office
AJMAN HOTEL BUILDING                                          IT Server Room
AJMAN HOTEL BUILDING                                        JUNIOR BOARDROOM
AJMAN HOTEL BUILDING                                               KIDS CLUB
AJMAN HOTEL BUILDING                                          KIDS POOL AREA
AJMAN HOTEL BUILDING                                        KITCHEN ENTRANCE
AJMAN HOTEL BUILDING                                          Kids Play Area
AJMAN HOTEL BUILDING                                                 Kitchen
AJMAN HOTEL BUILDING                                            LAUNDRY ROOM
AJMAN HOTEL BUILDING                                                LG FLOOR
AJMAN HOTEL BUILDING                                                LG Floor
AJMAN HOTEL BUILDING                                                   LOBBY
AJMAN HOTEL BUILDING                                              LOBBY AREA
AJMAN HOTEL BUILDING                                         LOBBY CORRIDORE
AJMAN HOTEL BUILDING                                      LOBBY SITTING AREA
AJMAN HOTEL BUILDING                                       LOBBY VALLET DESK
AJMAN HOTEL BUILDING                    LOSS AND FOUND VALUABLE SAFEBOX ROOM
AJMAN HOTEL BUILDING                             LOW VOLTAGE ELECTRICAL ROOM
AJMAN HOTEL BUILDING                                       LPG GAS TANK AREA
AJMAN HOTEL BUILDING                                            LUGGAGE ROOM
AJMAN HOTEL BUILDING                                                 LV ROOM
AJMAN HOTEL BUILDING                                        LV ROOM CORRIDOR
AJMAN HOTEL BUILDING                                       LV ROOM CORRIDORE
AJMAN HOTEL BUILDING                                            Laguage Room
AJMAN HOTEL BUILDING                                                Laundery
AJMAN HOTEL BUILDING                                                   Lobby
AJMAN HOTEL BUILDING                                       M FLOOR SL3 LOBBY
AJMAN HOTEL BUILDING                                      MAIN ENTRANCE ARCH
AJMAN HOTEL BUILDING                                      MAIN ENTRANCE DOOR
AJMAN HOTEL BUILDING                              MAIN ENTRANCE GENERAL VIEW
AJMAN HOTEL BUILDING                                               MAIN GATE
AJMAN HOTEL BUILDING                                          MAIN GATE AREA
AJMAN HOTEL BUILDING                                 MAIN GATE SECURITY ROOM
AJMAN HOTEL BUILDING                                     MAIN KITCHEN BAKERY
AJMAN HOTEL BUILDING                                  MAIN KITCHEN CORRIDORE
AJMAN HOTEL BUILDING                                          MAIN ROAD VIEW
AJMAN HOTEL BUILDING                                 MAIN SERVICE LIFT LOBBY
AJMAN HOTEL BUILDING                                                MAJLIS 1
AJMAN HOTEL BUILDING                                                MAJLIS 2
AJMAN HOTEL BUILDING                                            MAJLIS 3 & 4
AJMAN HOTEL BUILDING                                         MECHANICAL ROOM
AJMAN HOTEL BUILDING                                    MEJHANA CASH COUNTER
AJMAN HOTEL BUILDING                                        MEJHANA ENTRANCE
AJMAN HOTEL BUILDING                                       MEJHANA OVER VIEW
AJMAN HOTEL BUILDING                                      MEJHANA RESTAURANT
AJMAN HOTEL BUILDING                                     MEP ELECTRICAL ROOM
AJMAN HOTEL BUILDING                                                MEP ROOM
AJMAN HOTEL BUILDING                                   MEP SERVICE CORRIDORE
AJMAN HOTEL BUILDING                                            MOCK UP ROOM
AJMAN HOTEL BUILDING                                          Main Entrancce
AJMAN HOTEL BUILDING                                           Main Entrance
AJMAN HOTEL BUILDING                                            Main Kitchen
AJMAN HOTEL BUILDING                                                 Majhana
AJMAN HOTEL BUILDING                                                  Majlis
AJMAN HOTEL BUILDING                                        Marketing Office
AJMAN HOTEL BUILDING                                                 Mejhana
AJMAN HOTEL BUILDING                                      NEAR BANQUET STORE
AJMAN HOTEL BUILDING                                   NEAR DIESEL TANK ROOM
AJMAN HOTEL BUILDING                                 NEAR IDF ROOM CORRIDORE
AJMAN HOTEL BUILDING                                                NEAR IRD
AJMAN HOTEL BUILDING                                    NEAR MALE PLANT ROOM
AJMAN HOTEL BUILDING                                     NEAR SERVICE LIFT 5
AJMAN HOTEL BUILDING                                        NEAR STAIRCASE 3
AJMAN HOTEL BUILDING                                        PASTRY CORRIDORE
AJMAN HOTEL BUILDING                                       PATHWAY EXIT DOOR
AJMAN HOTEL BUILDING                                  PATHWAY NEAR KIDS POOL
AJMAN HOTEL BUILDING                                PATHWAY NEAR STAIRCASE 5
AJMAN HOTEL BUILDING                                PATHWAY SMOKING AREA TOP
AJMAN HOTEL BUILDING                                                     PH1
AJMAN HOTEL BUILDING                                                PL LOBBY
AJMAN HOTEL BUILDING                                       PL LOBBY CORRIDOR
AJMAN HOTEL BUILDING                                              PLANT ROOM
AJMAN HOTEL BUILDING                                            POOL & BEACH
AJMAN HOTEL BUILDING                                  POOL EQUIPMENT STORAGE
AJMAN HOTEL BUILDING                                               POOL VIEW
AJMAN HOTEL BUILDING                                          PROJECTOR ROOM
AJMAN HOTEL BUILDING                                               PUMP ROOM
AJMAN HOTEL BUILDING                                                  Pantry
AJMAN HOTEL BUILDING                                                 Parking
AJMAN HOTEL BUILDING                                  RECEIVING OUTSIDE AREA
AJMAN HOTEL BUILDING                                        RECEPTION DESK 1
AJMAN HOTEL BUILDING                                        RECEPTION DESK 3
AJMAN HOTEL BUILDING                                        RECEPTION LOUNGE
AJMAN HOTEL BUILDING                                   RECEPTION MIDDLE DESK
AJMAN HOTEL BUILDING                                      RESERVATION OFFICE
AJMAN HOTEL BUILDING                                          REVENUE OFFICE
AJMAN HOTEL BUILDING                                               Ramp Room
AJMAN HOTEL BUILDING                                          Receiving Area
AJMAN HOTEL BUILDING                                                 Rooftop
AJMAN HOTEL BUILDING                                            Rooftop Exit
AJMAN HOTEL BUILDING                                     S&M MANAGERS OFFICE
AJMAN HOTEL BUILDING                                       SAFI CASH COUNTER
AJMAN HOTEL BUILDING                                       SAFI GENERAL VIEW
AJMAN HOTEL BUILDING                                     SAFI GENERAL VIEW 1
AJMAN HOTEL BUILDING                                            SAFI KITCHEN
AJMAN HOTEL BUILDING                                   SALES DIRECTOR OFFICE
AJMAN HOTEL BUILDING                                           SECURITY ROOM
AJMAN HOTEL BUILDING                                   SERVER ROOM CORRIDORE
AJMAN HOTEL BUILDING                                          SERVICE LIFT 1
AJMAN HOTEL BUILDING                                          SERVICE LIFT 2
AJMAN HOTEL BUILDING                                          SERVICE LIFT 3
AJMAN HOTEL BUILDING                                    SERVICE LIFT 3 LOBBY
AJMAN HOTEL BUILDING                                          SERVICE LIFT 4
AJMAN HOTEL BUILDING                                    SERVICE LIFT 4 LOBBY
AJMAN HOTEL BUILDING                                          SERVICE LIFT 6
AJMAN HOTEL BUILDING                                    SERVICE LIFT 6 LOBBY
AJMAN HOTEL BUILDING                                      SERVICE LIFT LOBBY
AJMAN HOTEL BUILDING                                       SERVICE LIFT SIDE
AJMAN HOTEL BUILDING                                          SERVICE ROAD 1
AJMAN HOTEL BUILDING                                          SERVICE ROAD 2
AJMAN HOTEL BUILDING                                          SERVICE ROAD 3
AJMAN HOTEL BUILDING                               SERVICE ROAD EXIT BARRIER
AJMAN HOTEL BUILDING                                     SHJLCAP01-01-101(G)
AJMAN HOTEL BUILDING                                     SHJLCAP01-02-201(G)
AJMAN HOTEL BUILDING                                     SHJLCAP01-03-301(G)
AJMAN HOTEL BUILDING                                     SHJLCAP01-04-401(G)
AJMAN HOTEL BUILDING                                     SHJLCAP01-05-501(G)
AJMAN HOTEL BUILDING                                     SHJLCAP01-06-601(G)
AJMAN HOTEL BUILDING                                     SHJLCAP01-07-701(G)
AJMAN HOTEL BUILDING                                     SHJLCAP01-08-801(G)
AJMAN HOTEL BUILDING                                     SHJLCAP01-09-901(G)
AJMAN HOTEL BUILDING                              SHJLCAP01-BF-Chiller_Rm(B)
AJMAN HOTEL BUILDING                        SHJLCAP01-LG-Male_Changing_Rm(P)
AJMAN HOTEL BUILDING                                    SHJLCAP01-LG-ST10(G)
AJMAN HOTEL BUILDING                                  SHJLCAP01-MF-IDF_M2(C)
AJMAN HOTEL BUILDING SHJLCAP01-SF-Multipurpose_Treatment_Rm_Corridor_Male(S)
AJMAN HOTEL BUILDING                                     SHJLCAP02-01-102(G)
AJMAN HOTEL BUILDING                                     SHJLCAP02-02-202(G)
AJMAN HOTEL BUILDING                                     SHJLCAP02-03-302(G)
AJMAN HOTEL BUILDING                                     SHJLCAP02-04-402(G)
AJMAN HOTEL BUILDING                                     SHJLCAP02-05-502(G)
AJMAN HOTEL BUILDING                                     SHJLCAP02-06-602(G)
AJMAN HOTEL BUILDING                                     SHJLCAP02-07-702(G)
AJMAN HOTEL BUILDING                                     SHJLCAP02-08-801(G)
AJMAN HOTEL BUILDING                                     SHJLCAP02-09-901(G)
AJMAN HOTEL BUILDING              SHJLCAP02-BF-STB_WATER_TREATMENT_Rm_CRD(B)
AJMAN HOTEL BUILDING                      SHJLCAP02-LG-Female_Changing_Rm(P)
AJMAN HOTEL BUILDING                         SHJLCAP02-MF-Pantry_Corridor(C)
AJMAN HOTEL BUILDING                      SHJLCAP02-SF-LoungeGallery-Male(S)
AJMAN HOTEL BUILDING                                 SHJLCAP02-UG-Stair-2(G)
AJMAN HOTEL BUILDING                                     SHJLCAP03-01-102(G)
AJMAN HOTEL BUILDING                                     SHJLCAP03-02-202(G)
AJMAN HOTEL BUILDING                                     SHJLCAP03-03-302(G)
AJMAN HOTEL BUILDING                                     SHJLCAP03-04-402(G)
AJMAN HOTEL BUILDING                                     SHJLCAP03-05-502(G)
AJMAN HOTEL BUILDING                                     SHJLCAP03-06-602(G)
AJMAN HOTEL BUILDING                                     SHJLCAP03-07-702(G)
AJMAN HOTEL BUILDING                                     SHJLCAP03-08-802(G)
AJMAN HOTEL BUILDING                                     SHJLCAP03-09-902(G)
AJMAN HOTEL BUILDING                                     SHJLCAP03-BF-GLL(B)
AJMAN HOTEL BUILDING                             SHJLCAP03-MF-Majlis1-CRD(C)
AJMAN HOTEL BUILDING                              SHJLCAP03-SF-Relax_Male(S)
AJMAN HOTEL BUILDING                                     SHJLCAP03-UG-SLL(B)
AJMAN HOTEL BUILDING                                     SHJLCAP04-01-103(G)
AJMAN HOTEL BUILDING                                     SHJLCAP04-02-203(G)
AJMAN HOTEL BUILDING                                     SHJLCAP04-03-303(G)
AJMAN HOTEL BUILDING                                     SHJLCAP04-04-403(G)
AJMAN HOTEL BUILDING                                     SHJLCAP04-05-503(G)
AJMAN HOTEL BUILDING                                     SHJLCAP04-06-603(G)
AJMAN HOTEL BUILDING                                     SHJLCAP04-07-703(G)
AJMAN HOTEL BUILDING                                     SHJLCAP04-08-802(G)
AJMAN HOTEL BUILDING                                     SHJLCAP04-09-902(G)
AJMAN HOTEL BUILDING                                 SHJLCAP04-BF-GLL_CRD(B)
AJMAN HOTEL BUILDING                               SHJLCAP04-LG-Kids_Club(P)
AJMAN HOTEL BUILDING                               SHJLCAP04-LG-kids_Pool(O)
AJMAN HOTEL BUILDING                                 SHJLCAP04-MF-Majlis1(C)
AJMAN HOTEL BUILDING                              SHJLCAP04-SF-Sauna_Male(S)
AJMAN HOTEL BUILDING                                 SHJLCAP04-UG-Stair_1(B)
AJMAN HOTEL BUILDING                                     SHJLCAP05-01-104(G)
AJMAN HOTEL BUILDING                                     SHJLCAP05-02-204(G)
AJMAN HOTEL BUILDING                                     SHJLCAP05-03-304(G)
AJMAN HOTEL BUILDING                                     SHJLCAP05-04-404(G)
AJMAN HOTEL BUILDING                                     SHJLCAP05-05-504(G)
AJMAN HOTEL BUILDING                                     SHJLCAP05-06-604(G)
AJMAN HOTEL BUILDING                                     SHJLCAP05-07-704(G)
AJMAN HOTEL BUILDING                                     SHJLCAP05-08-803(G)
AJMAN HOTEL BUILDING                                     SHJLCAP05-09-903(G)
AJMAN HOTEL BUILDING                               SHJLCAP05-BF-HK_Office(B)
AJMAN HOTEL BUILDING                          SHJLCAP05-LG-Food_transport(O)
AJMAN HOTEL BUILDING                             SHJLCAP05-MF-JR_Board_Rm(C)
AJMAN HOTEL BUILDING                             SHJLCAP05-SF-Saloon_male(S)
AJMAN HOTEL BUILDING                                SHJLCAP05-UG-Corridor(G)
AJMAN HOTEL BUILDING                                     SHJLCAP06-01-105(G)
AJMAN HOTEL BUILDING                                     SHJLCAP06-02-205(G)
AJMAN HOTEL BUILDING                                     SHJLCAP06-03-305(G)
AJMAN HOTEL BUILDING                                     SHJLCAP06-04-405(G)
AJMAN HOTEL BUILDING                                     SHJLCAP06-05-510(G)  # Corrected typo in user data for this line
AJMAN HOTEL BUILDING                                     SHJLCAP06-06-610(G)  # same
AJMAN HOTEL BUILDING                                     SHJLCAP06-07-710(G)
AJMAN HOTEL BUILDING                                     SHJLCAP06-08-804(G)
AJMAN HOTEL BUILDING                                     SHJLCAP06-09-904(G)
AJMAN HOTEL BUILDING                           SHJLCAP06-BF-CALORIFIER_RM(B)
AJMAN HOTEL BUILDING                                  SHJLCAP06-LG-Bakery(B)
AJMAN HOTEL BUILDING                                SHJLCAP06-MF-Majlis_2(C)
AJMAN HOTEL BUILDING                                     SHJLCAP06-SF-GLL(S)
AJMAN HOTEL BUILDING                             SHJLCAP06-UG-BAB_KITCHEN(R)
AJMAN HOTEL BUILDING                                     SHJLCAP07-01-106(G)
AJMAN HOTEL BUILDING                                     SHJLCAP07-02-206(G)
AJMAN HOTEL BUILDING                                     SHJLCAP07-03-306(G)
AJMAN HOTEL BUILDING                                     SHJLCAP07-04-406(G)
AJMAN HOTEL BUILDING                                     SHJLCAP07-05-506(G)
AJMAN HOTEL BUILDING                                     SHJLCAP07-06-606(G)
AJMAN HOTEL BUILDING                                     SHJLCAP07-07-706(G)
AJMAN HOTEL BUILDING                                     SHJLCAP07-08-805(G)
AJMAN HOTEL BUILDING                                     SHJLCAP07-09-905(G)
AJMAN HOTEL BUILDING                               SHJLCAP07-BF-IDF_B2_CR(B)
AJMAN HOTEL BUILDING                         SHJLCAP07-LG-Bakery_Corridor(B)
AJMAN HOTEL BUILDING                  SHJLCAP07-MF-CRD_Executive_Board_RM(C)
AJMAN HOTEL BUILDING                       SHJLCAP07-SF-Male_Couple_Suite(S)
AJMAN HOTEL BUILDING                      SHJLCAP07-UG-SAFI_REST_Corridor(R)
AJMAN HOTEL BUILDING                                     SHJLCAP08-01-107(G)
AJMAN HOTEL BUILDING                                     SHJLCAP08-02-207(G)
AJMAN HOTEL BUILDING                                     SHJLCAP08-03-307(G)
AJMAN HOTEL BUILDING                                     SHJLCAP08-04-407(G)
AJMAN HOTEL BUILDING                                     SHJLCAP08-05-507(G)
AJMAN HOTEL BUILDING                                     SHJLCAP08-06-607(G)
AJMAN HOTEL BUILDING                                     SHJLCAP08-07-707(G)
AJMAN HOTEL BUILDING                                     SHJLCAP08-08-805(G)
AJMAN HOTEL BUILDING                                     SHJLCAP08-09-905(G)
AJMAN HOTEL BUILDING                          SHJLCAP08-BF-EXEC_HK_OFFICE(B)
AJMAN HOTEL BUILDING                              SHJLCAP08-LG-SL_4_Lobby(B)
AJMAN HOTEL BUILDING                      SHJLCAP08-MF-Executive_Board_RM(C)
AJMAN HOTEL BUILDING                     SHJLCAP08-SF-Female_Couple_Suite(S)
AJMAN HOTEL BUILDING                           SHJLCAP08-UG-Hall_Corridor(B)
AJMAN HOTEL BUILDING                                     SHJLCAP09-01-108(G)
AJMAN HOTEL BUILDING                                     SHJLCAP09-02-208(G)
AJMAN HOTEL BUILDING                                     SHJLCAP09-03-308(G)
AJMAN HOTEL BUILDING                                     SHJLCAP09-04-408(G)
AJMAN HOTEL BUILDING                                     SHJLCAP09-05-508(G)
AJMAN HOTEL BUILDING                                     SHJLCAP09-06-608(G)
AJMAN HOTEL BUILDING                                     SHJLCAP09-07-708(G)
AJMAN HOTEL BUILDING                                     SHJLCAP09-08-807(G)
AJMAN HOTEL BUILDING                                     SHJLCAP09-09-907(G)
AJMAN HOTEL BUILDING                     SHJLCAP09-BF-Public_area_store_crdB
AJMAN HOTEL BUILDING                           SHJLCAP09-LG-HVAC_Corridor(B)
AJMAN HOTEL BUILDING                            SHJLCAP09-MF-WASH_RM_AREA(C)
AJMAN HOTEL BUILDING                                  SHJLCAP09-SF-OFFICE(S)
AJMAN HOTEL BUILDING                          SHJLCAP09-UG-Vista_Corridor(B)
AJMAN HOTEL BUILDING                                     SHJLCAP10-01-109(G)
AJMAN HOTEL BUILDING                                     SHJLCAP10-02-209(G)
AJMAN HOTEL BUILDING                                     SHJLCAP10-03-309(G)
AJMAN HOTEL BUILDING                                     SHJLCAP10-04-409(G)
AJMAN HOTEL BUILDING                                      SHJLCAP10-05-509(G)
AJMAN HOTEL BUILDING                                     SHJLCAP10-06-609(G)
AJMAN HOTEL BUILDING                                     SHJLCAP10-07-709(G)
AJMAN HOTEL BUILDING                                     SHJLCAP10-08-808(G)
AJMAN HOTEL BUILDING                                     SHJLCAP10-09-908(G)
AJMAN HOTEL BUILDING                                     SHJLCAP10-BF-SLL(B)
AJMAN HOTEL BUILDING                        SHJLCAP10-LG-General_Workshop(B)
AJMAN HOTEL BUILDING                           SHJLCAP10-MF-Prayer_RM_CRD(C)
AJMAN HOTEL BUILDING                                     SHJLCAP10-SF-SLL(S)
AJMAN HOTEL BUILDING                                     SHJLCAP11-01-110(G)
AJMAN HOTEL BUILDING                                     SHJLCAP11-02-210(G)
AJMAN HOTEL BUILDING                                     SHJLCAP11-03-310(G)
AJMAN HOTEL BUILDING                                     SHJLCAP11-04-410(G)
AJMAN HOTEL BUILDING                                     SHJLCAP11-05-510(G)
AJMAN HOTEL BUILDING                                     SHJLCAP11-06-610(G)
AJMAN HOTEL BUILDING                                     SHJLCAP11-07-710(G)
AJMAN HOTEL BUILDING                                     SHJLCAP11-08-809(G)
AJMAN HOTEL BUILDING                                     SHJLCAP11-09-909(G)
AJMAN HOTEL BUILDING                               SHJLCAP11-BF-VIP_LOBBY(B)
AJMAN HOTEL BUILDING                         SHJLCAP11-LG-Workshop_Office(B)
AJMAN HOTEL BUILDING                          SHJLCAP11-MF-Male_Prayer_Rm(C)
AJMAN HOTEL BUILDING                           SHJLCAP11-MF-Prayer_RM_CRD(C)
AJMAN HOTEL BUILDING               SHJLCAP11-SF-RELAX/WAITING_AREA_FEMALE(S)
AJMAN HOTEL BUILDING                                 SHJLCAP11-UG-Diswash(B)
AJMAN HOTEL BUILDING                                     SHJLCAP12-01-111(G)
AJMAN HOTEL BUILDING                                     SHJLCAP12-02-211(G)
AJMAN HOTEL BUILDING                                     SHJLCAP12-03-311(G)
AJMAN HOTEL BUILDING                                     SHJLCAP12-04-411(G)
AJMAN HOTEL BUILDING                                     SHJLCAP12-05-511(G)
AJMAN HOTEL BUILDING                                        SHJLCAP12-06-611
AJMAN HOTEL BUILDING                                     SHJLCAP12-07-711(G)
AJMAN HOTEL BUILDING                                     SHJLCAP12-08-810(G)
AJMAN HOTEL BUILDING                                     SHJLCAP12-09-910(G)
AJMAN HOTEL BUILDING                               SHJLCAP12-BF-Boiler_Rm(B)
AJMAN HOTEL BUILDING                               SHJLCAP12-LG-HR_Office(B)
AJMAN HOTEL BUILDING                 SHJLCAP12-MF-Banquit_Caption_Manager(C)
AJMAN HOTEL BUILDING                    SHJLCAP12-SF-LoungeGallery_Female(S)
AJMAN HOTEL BUILDING                            SHJLCAP12-UG-IDF_Corridor(B)
AJMAN HOTEL BUILDING                                     SHJLCAP13-01-112(G)
AJMAN HOTEL BUILDING                                     SHJLCAP13-02-212(G)
AJMAN HOTEL BUILDING                                     SHJLCAP13-03-312(G)
AJMAN HOTEL BUILDING                                     SHJLCAP13-04-412(G)
AJMAN HOTEL BUILDING                                     SHJLCAP13-05-512(G)
AJMAN HOTEL BUILDING                                     SHJLCAP13-06-612(G)
AJMAN HOTEL BUILDING                                     SHJLCAP13-07-712(G)
AJMAN HOTEL BUILDING                                     SHJLCAP13-08-811(G)
AJMAN HOTEL BUILDING                                     SHJLCAP13-09-911(G)
AJMAN HOTEL BUILDING                  SHJLCAP13-BF-MEP_RM_CENTRAL_BATTERY(B)
AJMAN HOTEL BUILDING                     SHJLCAP13-LG-Accounting_Corridor(B)
AJMAN HOTEL BUILDING                                     SHJLCAP13-MF-SLL(C)
AJMAN HOTEL BUILDING        SHJLCAP13-SF-Multipurpose_treatment_Rm_Female(S)
AJMAN HOTEL BUILDING                       SHJLCAP13-UG-Satellite_Kitchen(R)
AJMAN HOTEL BUILDING                                     SHJLCAP14-01-114(G)
AJMAN HOTEL BUILDING                                     SHJLCAP14-02-214(G)
AJMAN HOTEL BUILDING                                     SHJLCAP14-03-314(G)
AJMAN HOTEL BUILDING                                     SHJLCAP14-04-414(G)
AJMAN HOTEL BUILDING                                     SHJLCAP14-05-514(G)
AJMAN HOTEL BUILDING                                     SHJLCAP14-06-614(G)
AJMAN HOTEL BUILDING                                     SHJLCAP14-07-714(G)
AJMAN HOTEL BUILDING                                     SHJLCAP14-08-812(G)
AJMAN HOTEL BUILDING                                     SHJLCAP14-09-912(G)
AJMAN HOTEL BUILDING                                 SHJLCAP14-BF-LAUNDRY(B)
AJMAN HOTEL BUILDING                         SHJLCAP14-LG-Accounts_Office(B)
AJMAN HOTEL BUILDING                         SHJLCAP14-MF-Sales_lounge_Rm(C)
AJMAN HOTEL BUILDING                            SHJLCAP14-SF-Sauna_Female(S)
AJMAN HOTEL BUILDING                            SHJLCAP14-UG-Front_Office(L)
AJMAN HOTEL BUILDING                                     SHJLCAP15-01-115(G)
AJMAN HOTEL BUILDING                                     SHJLCAP15-02-215(G)
AJMAN HOTEL BUILDING                                     SHJLCAP15-03-315(G)
AJMAN HOTEL BUILDING                                     SHJLCAP15-04-415(G)
AJMAN HOTEL BUILDING                                     SHJLCAP15-05-515(G)
AJMAN HOTEL BUILDING                                     SHJLCAP15-06-615(G)
AJMAN HOTEL BUILDING                                     SHJLCAP15-07-715(G)
AJMAN HOTEL BUILDING                                     SHJLCAP15-08-812(G)
AJMAN HOTEL BUILDING                                     SHJLCAP15-09-912(G)
AJMAN HOTEL BUILDING                                 SHJLCAP15-BF-STAIR_3(B)
AJMAN HOTEL BUILDING                              SHJLCAP15-LG-Eng_Toilet(B)
AJMAN HOTEL BUILDING                        SHJLCAP15-MF-CRD-Sales_lounge(C)
AJMAN HOTEL BUILDING                                    SHJLCAP15-MF-ST02(G)
AJMAN HOTEL BUILDING                           SHJLCAP15-SF-Creek_View_01(O)
AJMAN HOTEL BUILDING                                    SHJLCAP15-UG-Cafe(R)
AJMAN HOTEL BUILDING                                     SHJLCAP16-01-116(G)
AJMAN HOTEL BUILDING                                     SHJLCAP16-02-216(G)
AJMAN HOTEL BUILDING                                     SHJLCAP16-03-316(G)
AJMAN HOTEL BUILDING                                     SHJLCAP16-04-416(G)
AJMAN HOTEL BUILDING                                     SHJLCAP16-05-516(G)
AJMAN HOTEL BUILDING                                     SHJLCAP16-06-616(G)
AJMAN HOTEL BUILDING                                     SHJLCAP16-07-716(G)
AJMAN HOTEL BUILDING                                     SHJLCAP16-08-812(G)
AJMAN HOTEL BUILDING                                     SHJLCAP16-09-912(G)
AJMAN HOTEL BUILDING                                 SHJLCAP16-BF-Stair_1(B)
AJMAN HOTEL BUILDING                            SHJLCAP16-LG-Squash_Court(P)
AJMAN HOTEL BUILDING                               SHJLCAP16-MF-GM_Office(B)
AJMAN HOTEL BUILDING                           SHJLCAP16-SF-Creek_View_02(O)
AJMAN HOTEL BUILDING                          SHJLCAP16-UG-Souq_Courtyard(P)
AJMAN HOTEL BUILDING                                     SHJLCAP17-01-117(G)
AJMAN HOTEL BUILDING                                     SHJLCAP17-02-217(G)
AJMAN HOTEL BUILDING                                     SHJLCAP17-03-317(G)
AJMAN HOTEL BUILDING                                     SHJLCAP17-04-417(G)
AJMAN HOTEL BUILDING                                     SHJLCAP17-05-517(G)
AJMAN HOTEL BUILDING                                     SHJLCAP17-06-617(G)
AJMAN HOTEL BUILDING                                     SHJLCAP17-07-717(G)
AJMAN HOTEL BUILDING                                     SHJLCAP17-08-814(G)
AJMAN HOTEL BUILDING                                     SHJLCAP17-09-914(G)
AJMAN HOTEL BUILDING                                 SHJLCAP17-BF-Stair_4(B)
AJMAN HOTEL BUILDING                              SHJLCAP17-LG-Nr_Stair_4(B)
AJMAN HOTEL BUILDING                                     SHJLCAP17-MF-GLL(C)
AJMAN HOTEL BUILDING                               SHJLCAP17-SPA-Corridor(P)
AJMAN HOTEL BUILDING                            SHJLCAP17-UG-ATM_Corridor(P)
AJMAN HOTEL BUILDING                                     SHJLCAP18-01-118(G)
AJMAN HOTEL BUILDING                                     SHJLCAP18-02-218(G)
AJMAN HOTEL BUILDING                                     SHJLCAP18-03-318(G)
AJMAN HOTEL BUILDING                                     SHJLCAP18-04-418(G)
AJMAN HOTEL BUILDING                                     SHJLCAP18-05-518(G)
AJMAN HOTEL BUILDING                                     SHJLCAP18-06-618(G)
AJMAN HOTEL BUILDING                                     SHJLCAP18-07-718(G)
AJMAN HOTEL BUILDING                                     SHJLCAP18-08-815(G)
AJMAN HOTEL BUILDING                                     SHJLCAP18-09-915(G)
AJMAN HOTEL BUILDING                              SHJLCAP18-LG-S&M_office(B)
AJMAN HOTEL BUILDING                    SHJLCAP18-MF-GM_office_corridor_1(B)
AJMAN HOTEL BUILDING                               SHJLCAP18-SPA-Corridor(P)
AJMAN HOTEL BUILDING                                     SHJLCAP19-01-119(G)
AJMAN HOTEL BUILDING                                     SHJLCAP19-02-219(G)
AJMAN HOTEL BUILDING                                     SHJLCAP19-03-319(G)
AJMAN HOTEL BUILDING                                     SHJLCAP19-04-419(G)
AJMAN HOTEL BUILDING                                     SHJLCAP19-05-519(G)
AJMAN HOTEL BUILDING                                     SHJLCAP19-06-619(G)
AJMAN HOTEL BUILDING                                     SHJLCAP19-07-719(G)
AJMAN HOTEL BUILDING                                     SHJLCAP19-08-816(G)
AJMAN HOTEL BUILDING                                     SHJLCAP19-09-917(G)
AJMAN HOTEL BUILDING                              SHJLCAP19-LG-Eng_Office(B)
AJMAN HOTEL BUILDING                    SHJLCAP19-MF-GM_office_Corridor_2(B)
AJMAN HOTEL BUILDING                              SHJLCAP19-SPA-Reception(P)
AJMAN HOTEL BUILDING                        SHJLCAP19-UG-Ball_Room_Toilet(M)
AJMAN HOTEL BUILDING                               SHJLCAP19-UG-SAFI_Rest(R)
AJMAN HOTEL BUILDING                                     SHJLCAP20-01-120(G)
AJMAN HOTEL BUILDING                                     SHJLCAP20-02-220(G)
AJMAN HOTEL BUILDING                                     SHJLCAP20-03-320(G)
AJMAN HOTEL BUILDING                                     SHJLCAP20-04-420(G)
AJMAN HOTEL BUILDING                                     SHJLCAP20-05-520(G)
AJMAN HOTEL BUILDING                                     SHJLCAP20-06-620(G)
AJMAN HOTEL BUILDING                                     SHJLCAP20-07-720(G)
AJMAN HOTEL BUILDING                                     SHJLCAP20-08-817(G)
AJMAN HOTEL BUILDING                                     SHJLCAP20-09-919(G)
AJMAN HOTEL BUILDING                                 SHJLCAP20-BF-Stair_5(B)
AJMAN HOTEL BUILDING                         SHJLCAP20-LG-General_Cashier(B)
AJMAN HOTEL BUILDING                           SHJLCAP20-MF-Breakout_Area(C)
AJMAN HOTEL BUILDING                        SHJLCAP20-UG-Ball_Room_Toilet(F)
AJMAN HOTEL BUILDING                        SHJLCAP20-UG-Reception_Lounge(L)
AJMAN HOTEL BUILDING                                     SHJLCAP21-01-121(G)
AJMAN HOTEL BUILDING                                     SHJLCAP21-02-221(G)
AJMAN HOTEL BUILDING                                     SHJLCAP21-03-321(G)
AJMAN HOTEL BUILDING                                     SHJLCAP21-04-421(G)
AJMAN HOTEL BUILDING                                     SHJLCAP21-05-521(G)
AJMAN HOTEL BUILDING                                     SHJLCAP21-06-621(G)
AJMAN HOTEL BUILDING                                     SHJLCAP21-07-721(G)
AJMAN HOTEL BUILDING                                     SHJLCAP21-08-818(G)
AJMAN HOTEL BUILDING                                     SHJLCAP21-09-919(G)
AJMAN HOTEL BUILDING                              SHJLCAP21-BF-NR_Park_84(O)
AJMAN HOTEL BUILDING                                SHJLCAP21-BF-Stair_10(B)
AJMAN HOTEL BUILDING                            SHJLCAP21-LG-Corridor_F&B(B)
AJMAN HOTEL BUILDING                             SHJLCAP21-MF-CR_Majlis_4(C)
AJMAN HOTEL BUILDING                    SHJLCAP21-UG-Pre_Function_area_01(C)
AJMAN HOTEL BUILDING                                     SHJLCAP22-01-122(G)
AJMAN HOTEL BUILDING                                     SHJLCAP22-02-222(G)
AJMAN HOTEL BUILDING                                     SHJLCAP22-03-322(G)
AJMAN HOTEL BUILDING                                     SHJLCAP22-04-422(G)
AJMAN HOTEL BUILDING                                     SHJLCAP22-05-522(G)
AJMAN HOTEL BUILDING                                     SHJLCAP22-06-622(G)
AJMAN HOTEL BUILDING                                     SHJLCAP22-07-722(G)
AJMAN HOTEL BUILDING                                     SHJLCAP22-08-819(G)
AJMAN HOTEL BUILDING                              SHJLCAP22-BF-NR_Park_18(O)
AJMAN HOTEL BUILDING                           SHJLCAP22-LG-Staff_Canteen(B)
AJMAN HOTEL BUILDING                                SHJLCAP22-MF-Majlis_3(C)
AJMAN HOTEL BUILDING                                  SHJLCAP22-UG-Majlis(C)
AJMAN HOTEL BUILDING                                     SHJLCAP23-01-123(G)
AJMAN HOTEL BUILDING                                     SHJLCAP23-02-223(G)
AJMAN HOTEL BUILDING                                     SHJLCAP23-03-323(G)
AJMAN HOTEL BUILDING                                     SHJLCAP23-04-423(G)
AJMAN HOTEL BUILDING                                     SHJLCAP23-05-523(G)
AJMAN HOTEL BUILDING                                     SHJLCAP23-06-623(G)
AJMAN HOTEL BUILDING                                     SHJLCAP23-07-723(G)
AJMAN HOTEL BUILDING                                     SHJLCAP23-09-920(G)
AJMAN HOTEL BUILDING                                      SHJLCAP23-8-819(B)
AJMAN HOTEL BUILDING                             SHJLCAP23-BF-NR_Park_187(O)
AJMAN HOTEL BUILDING                        SHJLCAP23-LG-Female_Locker_Rm(B)
AJMAN HOTEL BUILDING                                SHJLCAP23-MF-Majlis_4(C)
AJMAN HOTEL BUILDING                           SHJLCAP23-UG-Mejhana_Court(O)
AJMAN HOTEL BUILDING                                     SHJLCAP24-01-124(G)
AJMAN HOTEL BUILDING                                     SHJLCAP24-02-224(G)
AJMAN HOTEL BUILDING                                     SHJLCAP24-03-324(G)
AJMAN HOTEL BUILDING                                     SHJLCAP24-04-424(G)
AJMAN HOTEL BUILDING                                     SHJLCAP24-05-524(G)
AJMAN HOTEL BUILDING                                     SHJLCAP24-06-624(G)
AJMAN HOTEL BUILDING                                     SHJLCAP24-07-724(G)
AJMAN HOTEL BUILDING                                     SHJLCAP24-08-820(G)
AJMAN HOTEL BUILDING                                     SHJLCAP24-09-920(G)
AJMAN HOTEL BUILDING                             SHJLCAP24-BF-NR_Park_124(O)
AJMAN HOTEL BUILDING                          SHJLCAP24-LG-Male_Locker_Rm(B)
AJMAN HOTEL BUILDING                      SHJLCAP24-MF-Cooling_Tower_Area(O)
AJMAN HOTEL BUILDING                                 SHJLCAP24-UG-MEJHANA(C)
AJMAN HOTEL BUILDING                                     SHJLCAP25-01-124(G)
AJMAN HOTEL BUILDING                                     SHJLCAP25-02-224(G)
AJMAN HOTEL BUILDING                                     SHJLCAP25-03-324(G)
AJMAN HOTEL BUILDING                                     SHJLCAP25-04-424(G)
AJMAN HOTEL BUILDING                                     SHJLCAP25-05-524(G)
AJMAN HOTEL BUILDING                                     SHJLCAP25-06-624(G)
AJMAN HOTEL BUILDING                                     SHJLCAP25-07-724(G)
AJMAN HOTEL BUILDING                                     SHJLCAP25-08-821(G)
AJMAN HOTEL BUILDING                                     SHJLCAP25-09-920(G)
AJMAN HOTEL BUILDING                     SHJLCAP25-BF-PLANT_RM_COLD_WATER(B)
AJMAN HOTEL BUILDING                        SHJLCAP25-LG-Associate_Lounge(B)
AJMAN HOTEL BUILDING                                     SHJLCAP25-MF-GYM(P)
AJMAN HOTEL BUILDING                        SHJLCAP25-UG-SAFI_Wash_RM_CRD(P)
AJMAN HOTEL BUILDING                                     SHJLCAP26-01-125(G)
AJMAN HOTEL BUILDING                                     SHJLCAP26-02-225(G)
AJMAN HOTEL BUILDING                                     SHJLCAP26-03-325(G)
AJMAN HOTEL BUILDING                                     SHJLCAP26-04-425(G)
AJMAN HOTEL BUILDING                                     SHJLCAP26-05-525(G)
AJMAN HOTEL BUILDING                                     SHJLCAP26-06-625(G)
AJMAN HOTEL BUILDING                                     SHJLCAP26-07-725(G)
AJMAN HOTEL BUILDING                                     SHJLCAP26-08-821(G)
AJMAN HOTEL BUILDING                                  SHJLCAP26-09-904_CR(G)
AJMAN HOTEL BUILDING                                SHJLCAP26-BF-PLANT_RM(B)
AJMAN HOTEL BUILDING                  SHJLCAP26-LG-General_Store_Corridor(B)
AJMAN HOTEL BUILDING                                     SHJLCAP26-MF-GYM(P)
AJMAN HOTEL BUILDING                    SHJLCAP26-UG-Pre_Function_area_02(C)
AJMAN HOTEL BUILDING                                  SHJLCAP27-01-104_CR(G)
AJMAN HOTEL BUILDING                                  SHJLCAP27-02-204_CR(G)
AJMAN HOTEL BUILDING                                  SHJLCAP27-03-304_CR(G)
AJMAN HOTEL BUILDING                                  SHJLCAP27-04-404_CR(G)
AJMAN HOTEL BUILDING                                  SHJLCAP27-05-504_CR(G)
AJMAN HOTEL BUILDING                                  SHJLCAP27-06-604_CR(G)
AJMAN HOTEL BUILDING                                  SHJLCAP27-07-704_CR(G)
AJMAN HOTEL BUILDING                                  SHJLCAP27-08-804_CR(G)
AJMAN HOTEL BUILDING                                  SHJLCAP27-09-912_CR(G)
AJMAN HOTEL BUILDING                              SHJLCAP27-LG-Uniform_Rm(B)
AJMAN HOTEL BUILDING                    SHJLCAP27-MF-GYM_MALE_CHANGING_RM(P)
AJMAN HOTEL BUILDING                               SHJLCAP27-UG-Vista_Res(R)
AJMAN HOTEL BUILDING                                  SHJLCAP28-01-112_CR(G)
AJMAN HOTEL BUILDING                                  SHJLCAP28-02-212_CR(G)
AJMAN HOTEL BUILDING                                  SHJLCAP28-03-312_CR(G)
AJMAN HOTEL BUILDING                                  SHJLCAP28-04-412_CR(G)
AJMAN HOTEL BUILDING                                  SHJLCAP28-05-512_CR(G)
AJMAN HOTEL BUILDING                                  SHJLCAP28-06-612_CR(G)
AJMAN HOTEL BUILDING                                  SHJLCAP28-07-712_CR(G)
AJMAN HOTEL BUILDING                                  SHJLCAP28-08-812_CR(G)
AJMAN HOTEL BUILDING                                  SHJLCAP28-09-917_CR(G)
AJMAN HOTEL BUILDING                     SHJLCAP28-LG-Uniform_Rm_Corridor(B)
AJMAN HOTEL BUILDING                  SHJLCAP28-MF-GYM_FEMALE_CHANGING_RM(P)
AJMAN HOTEL BUILDING                             SHJLCAP28-UG-Vista_Res_B(R)
AJMAN HOTEL BUILDING                                  SHJLCAP29-01-120_CR(G)
AJMAN HOTEL BUILDING                                  SHJLCAP29-02-220_CR(G)
AJMAN HOTEL BUILDING                                  SHJLCAP29-03-320_CR(G)
AJMAN HOTEL BUILDING                                  SHJLCAP29-04-420_CR(G)
AJMAN HOTEL BUILDING                                  SHJLCAP29-05-520_CR(G)
AJMAN HOTEL BUILDING                                  SHJLCAP29-06-620_CR(G)
AJMAN HOTEL BUILDING                                  SHJLCAP29-07-720_CR(G)
AJMAN HOTEL BUILDING                                  SHJLCAP29-08-820_CR(G)
AJMAN HOTEL BUILDING                                     SHJLCAP29-09-SLL(G)
AJMAN HOTEL BUILDING                               SHJLCAP29-LG-IT_Office(B)
AJMAN HOTEL BUILDING                                    SHJLCAP29-MF-ST01(G)
AJMAN HOTEL BUILDING                                   SHJLCAP29-UG-BAB-A(C)
AJMAN HOTEL BUILDING                                     SHJLCAP30-01-SLL(G)
AJMAN HOTEL BUILDING                                     SHJLCAP30-02-SLL(G)
AJMAN HOTEL BUILDING                                     SHJLCAP30-03-SLL(G)
AJMAN HOTEL BUILDING                                     SHJLCAP30-04-SLL(G)
AJMAN HOTEL BUILDING                                     SHJLCAP30-05-SLL(G)
AJMAN HOTEL BUILDING                                     SHJLCAP30-06-SLL(G)
AJMAN HOTEL BUILDING                                     SHJLCAP30-07-SLL(G)
AJMAN HOTEL BUILDING                                     SHJLCAP30-08-SLL(G)
AJMAN HOTEL BUILDING                                     SHJLCAP30-09-GLL(G)
AJMAN HOTEL BUILDING                               SHJLCAP30-LG-Server_Rm(B)
AJMAN HOTEL BUILDING                                  SHJLCAP30-UG-ESCAPE(P)
AJMAN HOTEL BUILDING                                     SHJLCAP31-01-GLL(G)
AJMAN HOTEL BUILDING                                     SHJLCAP31-02-GLL(G)
AJMAN HOTEL BUILDING                                     SHJLCAP31-03-GLL(G)
AJMAN HOTEL BUILDING                                     SHJLCAP31-04-GLL(G)
AJMAN HOTEL BUILDING                                     SHJLCAP31-05-GLL(G)
AJMAN HOTEL BUILDING                                     SHJLCAP31-06-GLL(G)
AJMAN HOTEL BUILDING                                     SHJLCAP31-07-GLL(G)
AJMAN HOTEL BUILDING                                     SHJLCAP31-08-GLL(G)
AJMAN HOTEL BUILDING                                 SHJLCAP31-09-STAIR_1(G)
AJMAN HOTEL BUILDING                                  SHJLCAP31-LG-UPS_Rm(B)
AJMAN HOTEL BUILDING                             SHJLCAP31-UG-Coffee_Shop(R)
AJMAN HOTEL BUILDING                                 SHJLCAP32-01-Stair_1(G)
AJMAN HOTEL BUILDING                                 SHJLCAP32-03-Stair_1(G)
AJMAN HOTEL BUILDING                           SHJLCAP32-04-Guest_Lift_01(G)
AJMAN HOTEL BUILDING                                 SHJLCAP32-05-Stair_1(G)
AJMAN HOTEL BUILDING                                 SHJLCAP32-07-Stair_1(G)
AJMAN HOTEL BUILDING                                 SHJLCAP32-09-STAIR_2(G)
AJMAN HOTEL BUILDING                SHJLCAP32-LG-Purchase_office_corridor(B)
AJMAN HOTEL BUILDING                         SHJLCAP32-UG-Business_center(P)
AJMAN HOTEL BUILDING                                 SHJLCAP33-01-Stair_2(G)
AJMAN HOTEL BUILDING                                 SHJLCAP33-03-Stair_2(G)
AJMAN HOTEL BUILDING                           SHJLCAP33-04-Guest_Lift_01(G)
AJMAN HOTEL BUILDING                                 SHJLCAP33-05-Stair_2(G)
AJMAN HOTEL BUILDING                                 SHJLCAP33-07-Stair_2(G)
AJMAN HOTEL BUILDING                SHJLCAP33-LG-Security_office_corridor(B)
AJMAN HOTEL BUILDING                             SHJLCAP33-UG-Ball_Room_1(C)
AJMAN HOTEL BUILDING                           SHJLCAP34-04-Guest_Lift_01(G)
AJMAN HOTEL BUILDING                     SHJLCAP34-LG-Fire_Command_Center(B)
AJMAN HOTEL BUILDING                             SHJLCAP34-UG-Ball_Room_2(C)
AJMAN HOTEL BUILDING                         SHJLCAP35-04-Service_Lift_01(G)
AJMAN HOTEL BUILDING                        SHJLCAP35-LG-BallRoom_Storage(B)
AJMAN HOTEL BUILDING                             SHJLCAP35-UG-Ball_Room_3(C)
AJMAN HOTEL BUILDING                         SHJLCAP36-04-Service_Lift_02(G)
AJMAN HOTEL BUILDING                SHJLCAP36-UG-Main_Entrance_1_External(O)
AJMAN HOTEL BUILDING                                SHJLCAP37-04-VIP_lift(G)
AJMAN HOTEL BUILDING                          SHJLCAP37-LG-Trash_Corridor(B)
AJMAN HOTEL BUILDING                      SHJLCAP37-UG-Recreation_Counter(O)
AJMAN HOTEL BUILDING                                     SHJLCAP38-LG-SLL(B)
AJMAN HOTEL BUILDING                          SHJLCAP38-UG-Tennis_court-1(O)
AJMAN HOTEL BUILDING                        SHJLCAP39-LG-Kitchen_Corridor(B)
AJMAN HOTEL BUILDING                                   SHJLCAP39-UG-BAB_B(C)
AJMAN HOTEL BUILDING               SHJLCAP40-LG-Meat_Preparation_Corridor(B)
AJMAN HOTEL BUILDING           SHJLCAP40-UG-Rest_BAB_Outdoor_Sitting_Area(O)
AJMAN HOTEL BUILDING                       SHJLCAP41-LG-Near_Cold_Kitchen(B)
AJMAN HOTEL BUILDING                               SHJLCAP41-UG-PB_Shower(O)
AJMAN HOTEL BUILDING                                SHJLCAP42-LG-Plant_Rm(B)
AJMAN HOTEL BUILDING        SHJLCAP42-UG-Recreation_Counter_2_Directional(O)
AJMAN HOTEL BUILDING                            SHJLCAP43-LG-Cold_Kitchen(B)
AJMAN HOTEL BUILDING                SHJLCAP43-UG-Main_Entrance_2_External(O)
AJMAN HOTEL BUILDING                            SHJLCAP44-LG-Main_Kitchen(B)
AJMAN HOTEL BUILDING              SHJLCAP44-UG-Tennis_court_2_Directional(O)
AJMAN HOTEL BUILDING                     SHJLCAP45-LG-Freezer_Rm_Corridor(B)
AJMAN HOTEL BUILDING                                 SHJLCAP45-UG-Staircase3
AJMAN HOTEL BUILDING                                 SHJLCAP45-UG-Staircase4
AJMAN HOTEL BUILDING                               SHJLCAP46-LG-Dry_Store(B)
AJMAN HOTEL BUILDING              SHJLCAP47-LG-Stewarding_Office_Corridor(B)
AJMAN HOTEL BUILDING                           SHJLCAP48-LG-Electrical_Rm(B)
AJMAN HOTEL BUILDING                           SITTING AREA NEAR STAIRCASE 6
AJMAN HOTEL BUILDING                                            SMOKING AREA
AJMAN HOTEL BUILDING                                       SOFA SITTING AREA
AJMAN HOTEL BUILDING                                       SOILED LINEN ROOM
AJMAN HOTEL BUILDING                                          SOUQ COURTYARD
AJMAN HOTEL BUILDING                                           SOUQ ENTRANCE
AJMAN HOTEL BUILDING                              SPA EXIT AREA BALLROOM TOP
AJMAN HOTEL BUILDING                            SPA EXIT OPEN AREA NEAR PL-4
AJMAN HOTEL BUILDING                                      SPA Floor Backside
AJMAN HOTEL BUILDING                           SPA OPEN ARE NEAR STAIRCASE-4
AJMAN HOTEL BUILDING                              SPA OPEN AREA BALLROOM TOP
AJMAN HOTEL BUILDING                                           SPA RECEPTION
AJMAN HOTEL BUILDING                                    SPA RETAIL SHOP AREA
AJMAN HOTEL BUILDING                                                SPA ROOM
AJMAN HOTEL BUILDING                                        SPA STAIRCASE -2
AJMAN HOTEL BUILDING                                            SQUASH COURT
AJMAN HOTEL BUILDING                                          STAFF ENTRANCE
AJMAN HOTEL BUILDING                                            STAIRCASE -4
AJMAN HOTEL BUILDING                                             STAIRCASE 1
AJMAN HOTEL BUILDING                                            STAIRCASE 10
AJMAN HOTEL BUILDING                                             STAIRCASE 2
AJMAN HOTEL BUILDING                                             STAIRCASE 3
AJMAN HOTEL BUILDING                                             STAIRCASE 4
AJMAN HOTEL BUILDING                                             STAIRCASE 5
AJMAN HOTEL BUILDING                                             STAIRCASE-3
AJMAN HOTEL BUILDING                                             STAIRCASE-4
AJMAN HOTEL BUILDING                                        STATIONERY STORE
AJMAN HOTEL BUILDING                                STB WATER TREATMENT ROOM
AJMAN HOTEL BUILDING                                         STORE CORRIDORE
AJMAN HOTEL BUILDING                                              STORE ROOM
AJMAN HOTEL BUILDING                                SWIMMING POOL PLANT ROOM
AJMAN HOTEL BUILDING                                        SWITCH GEAR ROOM
AJMAN HOTEL BUILDING                                         Safi Restaurant
AJMAN HOTEL BUILDING                                           Security Room
AJMAN HOTEL BUILDING                                             Server Room
AJMAN HOTEL BUILDING                                          Spa plant room
AJMAN HOTEL BUILDING                                     Stevwariding Office
AJMAN HOTEL BUILDING                                            Storage Room
AJMAN HOTEL BUILDING                                            TELECOM ROOM
AJMAN HOTEL BUILDING                                             TIME OFFICE
AJMAN HOTEL BUILDING                                        TIME OFFICE room
AJMAN HOTEL BUILDING                                           TOWEL COUNTER
AJMAN HOTEL BUILDING                                      TOWEL COUNTER AREA
AJMAN HOTEL BUILDING                              TOWEL COUNTER GENERAL VIEW
AJMAN HOTEL BUILDING                                        TRANSFORMER ROOM
AJMAN HOTEL BUILDING                                            UNIFORM ROOM
AJMAN HOTEL BUILDING                                                UPS ROOM
AJMAN HOTEL BUILDING                                           VEHICLE ENTRY
AJMAN HOTEL BUILDING                                            VEHICLE EXIT
AJMAN HOTEL BUILDING                                                VIP LIFT
AJMAN HOTEL BUILDING                                          VIP LIFT LOBBY
AJMAN HOTEL BUILDING                                             VIP PARKING
AJMAN HOTEL BUILDING                                        VISITOR ENTRANCE
AJMAN HOTEL BUILDING                                               VISTA BAR
AJMAN HOTEL BUILDING                                       VISTA BAR COUNTER
AJMAN HOTEL BUILDING                                      VISTA CASH COUNTER
AJMAN HOTEL BUILDING                                    VISTA DISH WASH AREA
AJMAN HOTEL BUILDING                                    VISTA GENERAL VIEW 1
AJMAN HOTEL BUILDING                                    VISTA GENERAL VIEW 2
AJMAN HOTEL BUILDING                                        VISTA RESTAURANT
AJMAN HOTEL BUILDING                                          VISTA WASHROOM
AJMAN HOTEL BUILDING                                                   Vista
AJMAN HOTEL BUILDING                              WATER PLANT ROOM CORRIDORE
    """

    lines = [l.strip() for l in raw_data.split('\n') if l.strip()]
    
    created_count = 0
    skipped_count = 0
    
    # Header skip
    if lines and "SITE" in lines[0]:
        lines = lines[1:]

    for line in lines:
        # Split by heavy gap (3+ spaces)
        parts = re.split(r'\s{3,}', line)
        
        if len(parts) >= 2:
            first_part = parts[0].strip()
            location_name = parts[-1].strip().title() # Always use the last part as Location
            
            if location_name == "<Na>" or not location_name:
                continue

            # Now tackle Site and Building from first_part
            # Try splitting by 2+ spaces first
            subparts = re.split(r'\s{2,}', first_part)
            if len(subparts) >= 2:
                site_name = subparts[0].strip().title()
                building_name = subparts[1].strip().title()
            else:
                # Fallback: Guess first word is Site, rest is Building
                words = first_part.split()
                if len(words) >= 2:
                    site_name = words[0].title()
                    building_name = " ".join(words[1:]).title()
                else:
                    site_name = first_part.title()
                    building_name = "Default Building"

            # Database creation
            site, _ = Site.objects.get_or_create(region=region, name=site_name)
            building, _ = Building.objects.get_or_create(branch=branch, name=building_name)
            loc, created = Location.objects.get_or_create(site=site, building=building, name=location_name)
            
            if created:
                created_count += 1
            else:
                skipped_count += 1

    print(f"Successfully processed {created_count + skipped_count} lines.")
    print(f"Created {created_count} new locations.")
    print(f"Skipped {skipped_count} existing locations.")

if __name__ == '__main__':
    bulk_add_locations()
