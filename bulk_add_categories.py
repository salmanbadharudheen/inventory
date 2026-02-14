import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.core.models import Organization
from apps.assets.models import Category
from apps.users.models import User

def bulk_add():
    # 1. Ensure Org exists
    org, created = Organization.objects.get_or_create(
        name="TechCorp HQ",
        defaults={'slug': 'techcorp-hq'}
    )
    
    # 2. Ensure admin is linked (if not already)
    try:
        admin = User.objects.get(username='admin')
        if not admin.organization:
            admin.organization = org
            admin.save()
            print("Linked admin to TechCorp HQ")
    except User.DoesNotExist:
        pass

    # 3. List of categories to add
    raw_list = ['MATTRESS', 'ALARM CLOCK', 'TV', 'LUGGAGE RACK',
       'SOFA  & CUSHIONS', 'TABLE', 'CHAIR', 'LOCKER', 'FRIDGE', 'Table',
       'chair ', 'Tv', 'chair', ' Tv ', 'Bathroom Pouf ', 'TABLE CHAIR',
       'Bed Base Trolley', 'Bed Matress', 'sofa', 'Table Chair',
       'L Shape Sofa', 'Fridge', 'Writing Table Chair', 'Sofa', 'Table ',
       'Chair', 'SOFA', 'SOFA  ', 'SOFA ', 'L shape Sofa', 'Chair ',
       'tv ', 'Bed Mattress', 'POUF', 'long pouf ', 'Tv ', 'L SHAPE SOFA',
       'LAMP', ' LAMP', 'BALCONY TABLE', 'BALCONY CHAIR',
       'Fire Extinguisher CO2', 'Dry Chemical Powder', 'TUMBLE DRYER',
       'WASHING MACHINE', 'BARCODING MACHINE', 'HANGER RAIL',
       'COMPRESSOR', 'TROLLEY', 'LAUNDRY CART', 'RACK', 'CO2 ',
       'WORKSTATION DESK', 'METAL RACK', 'MONITOR', 'DESKTOP PC',
       'POS MACHINE', 'PRINTER', 'METAL CABINET', 'BUCKET TROLLEY',
       'DRAWER', 'CLOCK', 'CUPBOARD', 'PUMP', 'CO2 5KG', 'DCP 6KG',
       'VACCUM MACHINE', 'CLEANING MACHINE', 'FILTER', 'CO2',
       'AIR HANDLING UNIT', 'HVAC DRIVE', 'DRC 6KG', 'BATTERY',
       'Cleaning Equipment', 'Trolley', 'BABY CRIBS', 'BED BASE', 'Rack',
       'Baby Cribs', 'Air Treatment Equipment', 'Monitor', 'Sun Bed',
       'SUN BED', 'trolley', 'Alarm', 'TELEPHONE', 'COOLING TOWER',
       'PANEL', 'AERIAL WORK PLATFORM MACHINE', 'VACCUM CLEANER', 'AC',
       'DESK', 'WORK STATION', 'CABINET', 'UPS', 'CABIN', 'MINIBAR',
       'LAPTOP', 'SAFEBOX', 'METAL LOCKER', 'LEG CURL MACHINE',
       'LEG EXTENSION MACHINE', 'HYPEREXTENSION BENCH',
       'BACK EXTENSION MACHINE', 'CHEST PRESS MACHIE', 'PULLDOWN MACHINE',
       'RECLINE EXERCISE BIKE', 'ARTIS CLIMB', 'CROSS TRAINER',
       'SHOULDER PRESS', 'RUN TREADMILL', 'SMITH MACHINE', 'BENCH',
       'UPPER BODY PULLEY', 'SKILLUP', 'SKILLROW', 'STOOL', 'HOT CABI',
       'OXYGEN MACHINE', 'HOT STONE MACHINE', 'SWIM SUITE DRYER',
       'DISHWASHER', 'Desktop PC', 'ID Scanner', 'Cash Drawer',
       'Dishwasher', 'Stage Base', 'Stairs', 'Cabinate ',
       'Juice Dispenser', 'Water Dispenser', 'Toaster', 'First Aid Kit',
       'Ladder', 'Blender', 'Lamp', 'BABY CHAIR',
       'BEACH SAND CLEANING MACHINE', 'Beach Umbrella', 'Bellman Cart',
       'Roller Grill', 'Counter', 'Boiler', 'Hot Box', 'Stand',
       'TRASH BIN', 'POS SYSTEM', 'WALL LED LIGHT', 'PENDANT LIGHT',
       'WORKSTATION', 'COOLER', 'CUBE ICE MAKER', 'BEACH BLENDER',
       'HOT WARMER', 'ELECTRIC FRYER', 'TABLE ', 'COOKING RANGE',
       'WORKBENCH', 'FOOD WARMER', 'ELECTRIC GRILL', 'BLENDER',
       'THERMOMIX', 'KITCHEN SINK', 'UTILITY CART', 'SERVING STATION',
       'Weighing Machine', 'Chocolate Melting Machine', 'Chiller',
       'Bone Saw', 'Cabinate', 'Conveyer', 'Food Warmer', 'Pouf', 'Fan',
       'FAN', 'AC UNIT', 'FACIAL STEAMER', 'MICROWAVE OVEN', 'SIDE TABLE',
       'VANITY POUF', 'BAR CHAIR', 'BARBECUE GRILL', 'HIGH STOOL',
       'SIGNAGE SCREEN', 'MIXING CONSOLE', 'HDMI SWITCH',
       'PORTABLE DANCE FLOOR', 'WHITEBOARD', 'FLIP CHART',
       'RECEPTION DESK', 'AIR CONDITIONER', 'AIR CONDITIONER UNIT',
       'PELLET GRILL', 'RACK ', 'FOOD WARMER LAMP', 'Ice Maker', 'Oven',
       'Exhaust Hood', 'Freezer', 'Sink', 'Kitchen Counter Side Table',
       'Stove', 'Baking Rack', 'Salamander', 'Fryer', 'STOVE', 'Grill',
       'Hot Plate', 'Kitchen Counter Table', 'Induction', 'Stage',
       'ACCESS CONTROLLER', 'Switch', 'Trolley ', 'Extra Bed Mattress',
       'Coffee Machine', 'Pallet Jack', 'Charcol Grill', 'Printer',
       'PROJECTOR SCREEN', 'FILE CABIN', 'VACCUM CLANER',
       'Pyramid Gas Patio Heaters', 'Swimminh Pool Heat Pump Unit',
       'Laptop', 'Desktop', 'UMBRELLA', 'Minibar', 'EV Charging Station',
       'Dock In Station', 'CO2 6KG', 'AIR CONDITIONING UNIT', 'LADDER',
       'CAMERA', 'CCTV', 'Matress', 'Boat Decor', 'LIFEGUARD CHAIR',
       'Server', 'Mattress', 'WALKIE-TALKIE', 'STEP LADDER',
       'METAL CABIN', 'ACCESS POINT', 'Docking Station', 'Router',
       'Food Transport Trolley', 'EXTENSION LADDER', 'BEACH UMBRELLA',
       'DRY CHEMICAL POWDER', 'Refrigerator', 'Induction Cooker ',
       'Ice Bin', 'SWITCHGEAR TRANSFORMER FEEDER PANEL 1',
       'SWITCHGEAR TRANSFORMER FEEDER PANEL 2',
       'SWITCHGEAR TRANSFORMER FEEDER PANEL 3',
       'SWITCHGEAR TRANSFORMER FEEDER PANEL 4', 'DVD PLAYER', 'SWITCHER',
       'Waffle Maker', 'Chopper', 'Pasteuriser', 'Dispenser',
       'Chocolate Fountain', 'Cotton Candy Machine', 'FAX', 'Telephone',
       'AC Unit', 'Passport Scanner', 'Encoder', 'Scanner', 'SAFE LOCKER',
       'Umbrella', 'REVOLVING DOOR',
       'MERCEDES BENZ SPRINTER VAN PASSENGER', 'TOYOTA COASTER',
       'TESLA 3', 'DRESSING TABLE', 'COFFEE TABLE', 'BED SIDE TABLE',
       'TV TABLE', 'DINING TABLE', 'GAS  STOVE', 'Refrigiator',
       'Washing Machine', 'Cooking Range', 'Bed Side Table',
       'Dressing table', 'BED COAT', 'TV RACK', 'Threadmill',
       'Dumble Rack', 'DOCKING STATION']

    # 4. Clean and Normalize
    # We'll use Title Case for consistency, but strip all extra spaces
    cleaned_names = sorted(list(set(name.strip().title() for name in raw_list if name.strip())))
    
    existing_categories = set(Category.objects.filter(organization=org).values_list('name', flat=True).iterator())
    
    to_create = []
    for name in cleaned_names:
        if name not in existing_categories:
            to_create.append(Category(organization=org, name=name))
    
    if to_create:
        # Note: bulk_create won't trigger .save() which generates 'code'
        # We should create them normally or manually generate codes if we want to bulk create.
        # Since the list is relatively small (~200 items), normal creation is fine and safe for code generation.
        created_count = 0
        for cat in to_create:
            cat.save()
            created_count += 1
        print(f"Successfully created {created_count} new categories.")
    else:
        print("All categories already exist.")

if __name__ == '__main__':
    bulk_add()
