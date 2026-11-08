import math

# ==============================================================================
# 1. REGIONAL FEED DATABASE
# ==============================================================================
REGIONAL_FEEDS = {
    'Coastal Region': [
        {
            'name': 'Paddy Straw',
            'category': 'Dry Fodder',
            'dm_pct': 89.0,
            'cp_pct': 3.5,
            'tdn_pct': 42.0,
            'price': 3.50,
        },
        {
            'name': 'Hybrid Napier (CO-5)',
            'category': 'Green Fodder',
            'dm_pct': 18.0,
            'cp_pct': 9.5,
            'tdn_pct': 57.0,
            'price': 2.20,
        },
        {
            'name': 'Guinea Grass',
            'category': 'Green Fodder',
            'dm_pct': 20.0,
            'cp_pct': 8.0,
            'tdn_pct': 54.0,
            'price': 2.00,
        },
        {
            'name': 'Coconut / Copra Cake',
            'category': 'Concentrate',
            'dm_pct': 90.0,
            'cp_pct': 21.0,
            'tdn_pct': 76.0,
            'price': 31.00,
        },
        {
            'name': 'Deoiled Rice Bran',
            'category': 'Concentrate',
            'dm_pct': 89.0,
            'cp_pct': 13.0,
            'tdn_pct': 55.0,
            'price': 16.50,
        },
        {
            'name': 'Nandini Cattle Feed',
            'category': 'Concentrate',
            'dm_pct': 90.0,
            'cp_pct': 20.0,
            'tdn_pct': 72.0,
            'price': 24.50,
        },
    ],
    'Malnad Region': [
        {
            'name': 'Paddy Straw',
            'category': 'Dry Fodder',
            'dm_pct': 89.0,
            'cp_pct': 3.5,
            'tdn_pct': 42.0,
            'price': 3.50,
        },
        {
            'name': 'Hybrid Napier Red',
            'category': 'Green Fodder',
            'dm_pct': 18.0,
            'cp_pct': 9.2,
            'tdn_pct': 57.0,
            'price': 2.10,
        },
        {
            'name': 'Stylo Legume',
            'category': 'Green Fodder',
            'dm_pct': 22.0,
            'cp_pct': 14.0,
            'tdn_pct': 55.0,
            'price': 2.80,
        },
        {
            'name': 'Crushed Maize Grain',
            'category': 'Concentrate',
            'dm_pct': 88.0,
            'cp_pct': 9.0,
            'tdn_pct': 80.0,
            'price': 22.00,
        },
        {
            'name': 'Coconut Cake',
            'category': 'Concentrate',
            'dm_pct': 90.0,
            'cp_pct': 21.0,
            'tdn_pct': 76.0,
            'price': 30.00,
        },
        {
            'name': 'Nandini Cattle Feed',
            'category': 'Concentrate',
            'dm_pct': 90.0,
            'cp_pct': 20.0,
            'tdn_pct': 72.0,
            'price': 24.50,
        },
    ],
    'North Region': [
        {
            'name': 'Jowar Kadbi (Sorghum)',
            'category': 'Dry Fodder',
            'dm_pct': 88.0,
            'cp_pct': 5.0,
            'tdn_pct': 52.0,
            'price': 4.00,
        },
        {
            'name': 'Green Maize (African Tall)',
            'category': 'Green Fodder',
            'dm_pct': 22.0,
            'cp_pct': 8.5,
            'tdn_pct': 62.0,
            'price': 2.40,
        },
        {
            'name': 'Lucerne / Alfalfa',
            'category': 'Green Fodder',
            'dm_pct': 20.0,
            'cp_pct': 19.5,
            'tdn_pct': 63.0,
            'price': 3.50,
        },
        {
            'name': 'Cottonseed Cake',
            'category': 'Concentrate',
            'dm_pct': 90.0,
            'cp_pct': 24.0,
            'tdn_pct': 75.0,
            'price': 28.00,
        },
        {
            'name': 'Gram Chuni (Chickpea Husk)',
            'category': 'Concentrate',
            'dm_pct': 89.0,
            'cp_pct': 12.0,
            'tdn_pct': 58.0,
            'price': 12.00,
        },
        {
            'name': 'Nandini Cattle Feed',
            'category': 'Concentrate',
            'dm_pct': 90.0,
            'cp_pct': 20.0,
            'tdn_pct': 72.0,
            'price': 24.50,
        },
    ],
    'South Region': [
        {
            'name': 'Ragi Straw',
            'category': 'Dry Fodder',
            'dm_pct': 88.0,
            'cp_pct': 3.8,
            'tdn_pct': 44.0,
            'price': 4.50,
        },
        {
            'name': 'Sugarcane Tops',
            'category': 'Green Fodder',
            'dm_pct': 28.0,
            'cp_pct': 5.5,
            'tdn_pct': 48.0,
            'price': 1.50,
        },
        {
            'name': 'Hybrid Napier (CO-4)',
            'category': 'Green Fodder',
            'dm_pct': 18.0,
            'cp_pct': 9.0,
            'tdn_pct': 56.0,
            'price': 2.00,
        },
        {
            'name': 'Groundnut Haulms',
            'category': 'Dry Fodder',
            'dm_pct': 85.0,
            'cp_pct': 10.0,
            'tdn_pct': 50.0,
            'price': 5.50,
        },
        {
            'name': 'Groundnut Cake',
            'category': 'Concentrate',
            'dm_pct': 92.0,
            'cp_pct': 42.0,
            'tdn_pct': 79.0,
            'price': 34.00,
        },
        {
            'name': 'Nandini Cattle Feed',
            'category': 'Concentrate',
            'dm_pct': 90.0,
            'cp_pct': 20.0,
            'tdn_pct': 72.0,
            'price': 24.50,
        },
    ],
}

# ==============================================================================
# 2. ICAR NUTRITION CALCULATOR ENGINE
# ==============================================================================
BREED_FAT_PROFILES = {
    'Crossbreed (HF / Jersey)': 4.0,
    'Indigenous / Desi (Sahiwal/Gir)': 4.5,
    'Murrah Buffalo': 7.0,
}

LACTATION_ADJUSTMENTS = {
    'Early (1 - 100 days)': {
        'cp_mult': 1.12,
        'tdn_mult': 1.10,
        'note': '+12% CP / +10% TDN for negative energy balance',
    },
    'Mid (101 - 200 days)': {
        'cp_mult': 1.00,
        'tdn_mult': 1.00,
        'note': 'Standard production requirement',
    },
    'Late (> 200 days)': {
        'cp_mult': 0.95,
        'tdn_mult': 1.05,
        'note': '+5% TDN for body condition regain & gestation',
    },
}


def calculate_icar_requirements(
    weight_kg, breed_type, lactation_stage, milk_production_ltr, max_intake_kg
):
  metabolic_wt = math.pow(weight_kg, 0.75)
  fat_pct = BREED_FAT_PROFILES.get(breed_type, 4.0)
  adj = LACTATION_ADJUSTMENTS.get(
      lactation_stage, LACTATION_ADJUSTMENTS['Mid (101 - 200 days)']
  )

  cp_maint_g = 0.8 * metabolic_wt
  tdn_maint_g = 30.0 * metabolic_wt

  cp_prod_g = milk_production_ltr * (35.0 + (fat_pct - 3.5) * 10.0)
  tdn_prod_g = milk_production_ltr * (320.0 + (fat_pct - 3.5) * 30.0)

  total_cp_g = (cp_maint_g + cp_prod_g) * adj['cp_mult']
  total_tdn_g = (tdn_maint_g + tdn_prod_g) * adj['tdn_mult']

  estimated_max_dmi = (0.025 * weight_kg) + (0.1 * milk_production_ltr)
  effective_dmi_cap = min(max_intake_kg, estimated_max_dmi)

  return {
      'fat_pct': fat_pct,
      'cp_required_g': round(total_cp_g, 1),
      'tdn_required_g': round(total_tdn_g, 1),
      'dmi_capacity_kg': round(effective_dmi_cap, 2),
      'lactation_note': adj['note'],
  }


# ==============================================================================
# 3. PRECISION RATION FORMULATION LOGIC
# ==============================================================================
def generate_precision_ration(input_data):
  region = input_data['region']
  feeds = REGIONAL_FEEDS.get(region, REGIONAL_FEEDS['Coastal Region'])

  reqs = calculate_icar_requirements(
      weight_kg=input_data['weight_kg'],
      breed_type=input_data['breed_type'],
      lactation_stage=input_data['lactation_stage'],
      milk_production_ltr=input_data['milk_production_ltr'],
      max_intake_kg=input_data['daily_feed_intake_kg'],
  )

  green_feeds = [f for f in feeds if f['category'] == 'Green Fodder']
  dry_feeds = [f for f in feeds if f['category'] == 'Dry Fodder']
  conc_feeds = [f for f in feeds if f['category'] == 'Concentrate']

  green_qty = round(15.0 + (input_data['milk_production_ltr'] * 0.5), 1)
  dry_qty = round(4.0 + (input_data['weight_kg'] * 0.003), 1)
  conc_qty = round(2.0 + (input_data['milk_production_ltr'] * 0.35), 1)

  allocated_ration = []
  total_dm = 0.0
  total_cp = 0.0
  total_tdn = 0.0
  total_cost = 0.0

  if green_feeds:
    qty = green_qty / len(green_feeds)
    for f in green_feeds:
      allocated_ration.append((f, round(qty, 2)))

  if dry_feeds:
    qty = dry_qty / len(dry_feeds)
    for f in dry_feeds:
      allocated_ration.append((f, round(qty, 2)))

  if conc_feeds:
    c_qty1 = round(conc_qty * 0.6, 2)
    c_qty2 = round(conc_qty * 0.4, 2)
    allocated_ration.append((conc_feeds[-1], c_qty1))
    allocated_ration.append((conc_feeds[0], c_qty2))

  ration_rows = []
  for feed, fresh_kg in allocated_ration:
    if fresh_kg > 0:
      dm_kg = fresh_kg * (feed['dm_pct'] / 100.0)
      cp_g = dm_kg * (feed['cp_pct'] / 100.0) * 1000.0
      tdn_g = dm_kg * (feed['tdn_pct'] / 100.0) * 1000.0
      cost = fresh_kg * feed['price']

      total_dm += dm_kg
      total_cp += cp_g
      total_tdn += tdn_g
      total_cost += cost

      ration_rows.append({
          'Feed Name': feed['name'],
          'Category': feed['category'],
          'Fresh Qty (kg/day)': f'{fresh_kg:.2f}',
          'Price (₹/kg)': f"₹{feed['price']:.2f}",
          'Daily Cost (₹)': f'₹{cost:.2f}',
      })

  return {
      'inputs': input_data,
      'requirements': reqs,
      'ration_rows': ration_rows,
      'totals': {
          'total_dm_kg': round(total_dm, 2),
          'total_cp_g': round(total_cp, 1),
          'total_tdn_g': round(total_tdn, 1),
          'total_cost_rs': round(total_cost, 2),
      },
  }


# ==============================================================================
# 4. INTERACTIVE TERMINAL PROMPTS
# ==============================================================================
def get_user_inputs():
  print('\n' + '=' * 80)
  print('          ENTER ANIMAL PARAMETERS FOR PRECISION FEED OPTIMIZATION      ')
  print('=' * 80)

  # 1. Select Region
  regions = list(REGIONAL_FEEDS.keys())
  print('\n[1] Select Region:')
  for idx, r in enumerate(regions, 1):
    print(f'   {idx}. {r}')
  try:
    r_idx = int(input('Select Region (1-4) [Default 1]: ') or '1') - 1
    selected_region = (
        regions[r_idx] if 0 <= r_idx < len(regions) else regions[0]
    )
  except ValueError:
    selected_region = regions[0]

  # 2. Select Breed Type
  breeds = list(BREED_FAT_PROFILES.keys())
  print('\n[2] Select Breed Type:')
  for idx, b in enumerate(breeds, 1):
    print(f'   {idx}. {b}')
  try:
    b_idx = int(input('Select Breed (1-3) [Default 1]: ') or '1') - 1
    selected_breed = breeds[b_idx] if 0 <= b_idx < len(breeds) else breeds[0]
  except ValueError:
    selected_breed = breeds[0]

  # 3. Select Lactation Stage
  stages = list(LACTATION_ADJUSTMENTS.keys())
  print('\n[3] Select Lactation Stage:')
  for idx, s in enumerate(stages, 1):
    print(f'   {idx}. {s}')
  try:
    s_idx = int(input('Select Lactation Stage (1-3) [Default 1]: ') or '1') - 1
    selected_stage = stages[s_idx] if 0 <= s_idx < len(stages) else stages[0]
  except ValueError:
    selected_stage = stages[0]

  # 4. Numeric Inputs
  try:
    weight_kg = float(
        input('\n[4] Enter Body Weight (kg) [e.g. 480]: ') or '480'
    )
    milk_ltr = float(
        input('[5] Enter Milk Production (Liters/day) [e.g. 14]: ') or '14'
    )
    max_feed_kg = float(
        input('[6] Enter Max Fresh Feed Intake Limit (kg) [e.g. 30]: ') or '30'
    )
  except ValueError:
    weight_kg, milk_ltr, max_feed_kg = 480.0, 14.0, 30.0

  return {
      'weight_kg': weight_kg,
      'breed_type': selected_breed,
      'lactation_stage': selected_stage,
      'daily_feed_intake_kg': max_feed_kg,
      'milk_production_ltr': milk_ltr,
      'region': selected_region,
  }


# ==============================================================================
# 5. TERMINAL PRINT FORMATTER
# ==============================================================================
def print_terminal_output(result):
  inp = result['inputs']
  req = result['requirements']
  tot = result['totals']

  print('\n' + '=' * 80)
  print('              DAIRY PRECISION FEED OPTIMIZATION - TERMINAL BACKEND      ')
  print('=' * 80)

  print('\n[1. ANIMAL PROFILE & INPUT PARAMETERS]')
  print('-' * 80)
  print(f"  • Selected Region    : {inp['region']}")
  print(f"  • Animal Body Weight : {inp['weight_kg']} kg")
  print(
      f"  • Breed Type         : {inp['breed_type']} (Est. Fat:"
      f" {req['fat_pct']}%)"
  )
  print(f"  • Lactation Stage    : {inp['lactation_stage']}")
  print(f"  • Milk Production    : {inp['milk_production_ltr']} Liters/day")
  print(
      f"  • Daily Feed Limit   : {inp['daily_feed_intake_kg']} kg (Fresh basis)"
  )

  print('\n[2. ICAR NUTRITIONAL TARGETS & FULFILLMENT]')
  print('-' * 80)
  print(
      f"{'Nutrient Metric':<25} | {'Required Target':<18} | {'Provided in Ration':<18} | {'Status'}"
  )
  print('-' * 80)

  cp_status = '✅ MET' if tot['total_cp_g'] >= req['cp_required_g'] else '⚠️ LOW'
  tdn_status = (
      '✅ MET' if tot['total_tdn_g'] >= req['tdn_required_g'] else '⚠️ LOW'
  )
  dmi_status = (
      '✅ WITHIN CAP'
      if tot['total_dm_kg'] <= req['dmi_capacity_kg']
      else '⚠️ EXCEEDS CAP'
  )

  print(
      f"{'Crude Protein (CP)':<25} | {req['cp_required_g']:<13} g |"
      f' {tot["total_cp_g"]:<13} g | {cp_status}'
  )
  print(
      f"{'Energy (TDN)':<25} | {req['tdn_required_g']:<13} g |"
      f' {tot["total_tdn_g"]:<13} g | {tdn_status}'
  )
  print(
      f"{'Dry Matter Intake (DMI)':<25} | {req['dmi_capacity_kg']:<13} kg |"
      f' {tot["total_dm_kg"]:<13} kg | {dmi_status}'
  )
  print(f'  Note: {req["lactation_note"]}')

  print('\n[3. OPTIMIZED REGION-SPECIFIC FEED FORMULATION]')
  print('-' * 80)
  header = f"{'Feed Name':<26} | {'Category':<14} | {'Qty (kg/day)':<13} | {'Rate (₹/kg)':<11} | {'Daily Cost'}"
  print(header)
  print('-' * 80)

  for row in result['ration_rows']:
    print(
        f"{row['Feed Name']:<26} | {row['Category']:<14} | {row['Fresh Qty (kg/day)']:<13} | {row['Price (₹/kg)']:<11} | {row['Daily Cost (₹)']}"
    )

  print('-' * 80)
  print(
      f"{'TOTAL DAILY RATION COST (' + inp['region'] + '):':<58} ₹{tot['total_cost_rs']} / day"
  )
  print('=' * 80 + '\n')


# ==============================================================================
# 6. EXECUTION ENTRY POINT
# ==============================================================================
if __name__ == '__main__':
  # Interactive Input Gathering
  user_input = get_user_inputs()
  output = generate_precision_ration(user_input)
  print_terminal_output(output)