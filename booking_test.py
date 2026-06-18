name= input('Wendy')
date= input('29/12/2025:')
booking= f'Wendy booked for 15/12/2025\n'
with open('bookings.txt', 'a') as file:file.write(booking)
print('Booking saved successfully!')