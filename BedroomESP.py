import utime

patientCurfew = 18

# Get the current time
currentTime = utime.localtime()

# Get only the hour
currentHour = currentTime[3]

print("Current Time:", "{:02d}".format(currentHour))

if currentHour >= patientCurfew:
    #