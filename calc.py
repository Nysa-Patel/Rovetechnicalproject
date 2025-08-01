def calculate_value_per_point(cash_price, points_used, taxes_fees=0, label="Redemption"):
    """
    Calculate value per point or mile and allows user to answer.
    """
    print(f"\nQ: What is the value per point for a {label}?")
    print(f"Details:")
    print(f"- Cash price: ${cash_price}")
    print(f"- Points used: {points_used}")
    print(f"- Taxes/fees: ${taxes_fees}")

    net_value = cash_price - taxes_fees
    value_per_point = (net_value / points_used) * 100  #cents

    print(f"\nA: Value per point = (${cash_price} - ${taxes_fees}) / {points_used} = {round(value_per_point, 2)}¢ per point")
    return round(value_per_point, 2)


def get_redemption_input():
    """
    Ask user for redemption details and return them as appropriate types.
    """
    label = input("\nEnter a label for this redemption (e.g., Flight, Hotel, Gift Card): ")
    cash_price = float(input("Enter the full cash price of the service ($): "))
    points_used = int(input("Enter the number of points/miles used: "))
    taxes_fees = float(input("Enter the taxes or fees paid ($), if any (enter 0 if none): "))

    return cash_price, points_used, taxes_fees, label


# Run multiple times for multiple redemptions
num_redemptions = int(input("How many redemptions do you want to calculate? "))

all_results = []

for i in range(num_redemptions):
    print(f"\n Redemption #{i+1} ")
    cash_price, points_used, taxes_fees, label = get_redemption_input()
    value = calculate_value_per_point(cash_price, points_used, taxes_fees, label)
    all_results.append((label, value))

# Summary: best value
best = max(all_results, key=lambda x: x[1])

print("\n Summary:")
for label, value in all_results:
    print(f"- {label}: {value}¢ per point")

print(f"\n Best value: {best[0]} with {best[1]}¢ per point")

