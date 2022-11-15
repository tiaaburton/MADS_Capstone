import sec
import yahoo
import fred

print("Running Market Shopper Daily Update")
print("Updating FRED...")
fred.initialize_fred()
print("Updating SEC...")
sec.update_sec_daily()
print("Updating Yahoo...")
yahoo.update_yahoo_daily()
print("All datasets updated successfully")

print("Updating features...")
#sector update
