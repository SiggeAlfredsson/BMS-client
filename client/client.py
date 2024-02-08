'''
it takes 4 hours to charge the car from 20->80%
it can not charge at 11, 15-19, it exceeds 11kw
if i want the charge when its under 80cent a hour i need to charge beetween 22-23(23:59?) and 01-04 (04:59?)

make 3 buttons,
charge ->80%
charge under 11kW
charge under 80 cent/hour


NE not existence

BESS

amount of power that you need 

energy price convert to sek /2000 to get right

Pgrid(t) * Ecost(t)

n4*g4 = cost

summer day

1000*howbig(40)*effecenicy/(0,23) pv production

T1-T24


short explain 1-2 slides max ,
type of builsing
max power
located in gbg
energy price

Mostafa case study
House
SE3
Student, away from T7 and gets home at T14
74% and 39%



charging_power=7.4
max load = 11
11 - 7.4 = 3,6
,12 kwh / minute (second)
but also the baseload?

HOURS THAT IS OK TO CHARGE
baseload under 3,6
00 01 02 03 04 14 21 22 23

energyprice, startas när elpriset är som lägst
22 är det som lägst

I dont understand the current baseload in the server, it adds the charger power / seconds in a hour
should it not just add the charging power to the baseload ? so if it charges when the baseload is 4 the baseload is 11.4 ?
It does not seem correct?


when ev battery is at 20% it is at 9,26kW , to go to 80%(37,04kW) with 7,4 kW charger it needs to charge 3.75 hours (3 hours 45 min)
(calculation is 37,04-9,26 = 27,78 kw to charge | 27,78/7,4 = 3,75 )
'''


import tkinter as tk
from tkinter import Button, Frame, Label
import numpy as np
import requests
from matplotlib.figure import Figure 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg 

BASE_URL = "http://127.0.0.1:5000"

class EVChargeControllerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EV Charge Controller")
        
        # max values
        self.max_baseload = 3.6 #kW
        self.max_hourly_price = 80 #öre

        self.baseload_data = []
        self.price_per_hour_data = []
        self.sim_time_hour = 0
        self.sim_time_min = 0
        self.battery_percentage = 0
        self.base_current_load = 0
        self.battery_capacity_kWh = 0
        self.price_optimized_hours = []
        self.load_optimized_hours = []


        #booleans
        self.should_charge = False # charge whatever the load / price is
        self.load_optimized = False # charge only when the load is under max_baseload
        self.price_optimized = False # charge only when the price is under max_hourly_price

        self.create_widgets()
        self.fetch_data()
        self.plot_data()
        self.app_loop()

    def create_widgets(self):
        # Frame to contain labels, buttons, and battery canvas
        self.frame = Frame(self.root)
        self.frame.pack(pady=10)

        # Labels and buttons
        self.time_label = Label(self.frame, text="")
        self.time_label.grid(row=0, column=0, pady=5)

        self.battery_percentage_label = Label(self.frame, text="")
        self.battery_percentage_label.grid(row=1, column=0, pady=5)

        self.battery_capacity_kWh_label = Label(self.frame, text="")
        self.battery_capacity_kWh_label.grid(row=2, column=0, pady=5)

        self.base_current_load_label = Label(self.frame, text="")
        self.base_current_load_label.grid(row=3, column=0, pady=5)

        self.price_per_hour_label = Label(self.frame, text="")
        self.price_per_hour_label.grid(row=4, column=0, pady=5)

        self.start_button = Button(self.frame, text="Start Charge", command=self.start_charge)
        self.start_button.grid(row=5, column=0, pady=5)

        self.load_optimized_button = Button(self.frame, text="Start Load Optimized Charge", command=self.load_optimized_charge)
        self.load_optimized_button.grid(row=6, column=0, pady=5)

        self.price_optimized_button = Button(self.frame, text="Start Price Optimized Charge", command=self.price_optimized_charge)
        self.price_optimized_button.grid(row=7, column=0, pady=5)
        
        self.price_and_load_optimized_button = Button(self.frame, text="Start Price and Load Optimized Charge", command=self.price_and_load_optimized_charge)
        self.price_and_load_optimized_button.grid(row=8, column=0, pady=5)

        self.stop_button = Button(self.frame, text="Stop Charge", command=self.stop_all_charging)
        self.stop_button.grid(row=9, column=0, pady=5)

        self.discharge_button = Button(self.frame, text="Discharge Battery", command=self.discharge_battery)
        self.discharge_button.grid(row=10, column=0, padx=200)

        self.result_label = Label(self.frame, text="")
        self.result_label.grid(row=11, column=0, pady=5)

        # Battery canvas
        self.battery_canvas = tk.Canvas(self.frame, width=100, height=200, bg='white')
        self.battery_canvas.grid(row=0, column=1, rowspan=11, padx=20, pady=5)

        
    def plot_data(self):
        fig = Figure(figsize=(14, 4), dpi=100)
        self.ax1 = fig.add_subplot(121)
        self.ax2 = fig.add_subplot(122)

        # Adding a small offset to the x-coordinates for the bars
        bar_width = 0.9
        offset = bar_width / 2  # Adjust this offset as needed

        self.ax1.bar(np.arange(24) + offset, self.baseload_data, width=bar_width, label='Baseload', color='blue')
        self.ax1.set_xlabel('Hour')
        self.ax1.set_ylabel('Value')
        self.ax1.set_title('Baseload (kWh)')
        self.ax1.legend()
        self.ax1.set_xticks(range(24))
        self.ax1.set_yticks(range(12))

        self.ax2.bar(np.arange(24) + offset, self.price_per_hour_data, width=bar_width, label='Price per Hour', color='green')
        self.ax2.set_xlabel('Hour')
        self.ax2.set_ylabel('Cost')
        self.ax2.set_title('Price per Hour (öre)')
        self.ax2.legend()
        self.ax2.set_xticks(range(24))
        
        self.hourly_baseload_line = self.ax1.axhline(y=self.max_baseload, color='red', linestyle='-')
        self.hourly_price_line = self.ax2.axhline(y=self.max_hourly_price, color='red', linestyle='-')

        # Adding a line to represent the current time
        self.current_time_line_ax1 = self.ax1.axvline(color='black', linestyle='-')
        self.current_time_line_ax1.set_xdata(0)
        
        self.current_time_line_ax2 = self.ax2.axvline(color='black', linestyle='-')
        self.current_time_line_ax2.set_xdata(0)
        
        self.canvas = FigureCanvasTkAgg(fig, master=self.root)  
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)


        
    def draw_battery(self):
        battery_width = 80
        battery_height = 150
        battery_x = (100 - battery_width) / 2
        battery_y = 25

        # Clear previous battery
        self.battery_canvas.delete("battery")

        # Draw battery outline
        self.battery_canvas.create_rectangle(battery_x, battery_y, battery_x + battery_width, battery_y + battery_height, outline='black', tags="battery")

        # Calculate battery fill percentage
        fill_height = (battery_height - 10) * (self.battery_percentage / 100)

        # Determine fill color based on battery percentage
        if self.battery_percentage >= 60:
            fill_color = 'green'
        elif 30 <= self.battery_percentage < 60:
            fill_color = 'yellow'
        else:
            fill_color = 'red'

        # Draw battery fill
        self.battery_canvas.create_rectangle(battery_x + 5, battery_y + 5 + (battery_height - 10 - fill_height),
                                            battery_x + battery_width - 5, battery_y + battery_height - 5, fill=fill_color, tags="battery")



    def app_loop(self):
        self.update_info()
        
        if self.should_charge or self.load_optimized or self.price_optimized:
            self.control_charging()
            
        self.root.after(1000, self.app_loop)

    def update_info(self):
        # Fetch info from server
        info_data = self.get_info()
        
        # Update variables
        self.battery_percentage = self.get_charge_percentage()
        self.sim_time_hour = info_data.get('sim_time_hour', 0)
        self.sim_time_min = info_data.get('sim_time_min', 0)
        self.base_current_load = info_data.get('base_current_load', 0)
        self.battery_capacity_kWh = info_data.get('battery_capacity_kWh', 0)

        # Update labels
        self.time_label.config(text=f"Time: {self.sim_time_hour:02d}:{self.sim_time_min:02d}")
        self.battery_percentage_label.config(text=f"Charge Percentage: {self.battery_percentage}")
        self.base_current_load_label.config(text=f"Current baseload: {self.base_current_load}")
        self.battery_capacity_kWh_label.config(text=f"Battery Capacity in kWh: {self.battery_capacity_kWh}")
        self.price_per_hour_label.config(text=f"Price this hour (öre) : {self.price_per_hour_data[self.sim_time_hour]}")

        self.draw_battery()
        
        if self.sim_time_hour in self.price_optimized_hours:
            self.hourly_price_line.set_color('green')
        else:
            self.hourly_price_line.set_color('red')
            
        if self.sim_time_hour in self.load_optimized_hours:
            self.hourly_baseload_line.set_color('green')
        else:
            self.hourly_baseload_line.set_color('red')
            
            
    
        self.current_time_line_ax1.set_xdata(self.sim_time_hour+self.sim_time_min/60)
        self.current_time_line_ax2.set_xdata(self.sim_time_hour+self.sim_time_min/60)
        self.canvas.draw()

        
          
    def fetch_data(self):
        self.fetch_baseload()
        self.fetch_price_per_hour()

    def fetch_baseload(self):
        response = requests.get(f"{BASE_URL}/baseload")
        self.baseload_data.extend(response.json())
        self.load_optimized_hours = {i: val for i, val in enumerate(self.baseload_data) if val < self.max_baseload}


    def fetch_price_per_hour(self):
        response = requests.get(f"{BASE_URL}/priceperhour")
        self.price_per_hour_data.extend(response.json())
        self.price_optimized_hours = {i: val for i, val in enumerate(self.price_per_hour_data) if val < self.max_hourly_price}

    def get_info(self):
        response = requests.get(f"{BASE_URL}/info")
        return response.json()

    def get_charge_percentage(self):
        response = requests.get(f"{BASE_URL}/charge")
        return response.json()

    def start_charge(self):
        self.start_charging()
        self.should_charge = True
        self.result_label.config(text="Now charging")

    def stop_charge(self):
        self.stop_charging()
        self.result_label.config(text="Stopped charging, will start again soon when price/load is lower")

    def load_optimized_charge(self):
        self.load_optimized = True
        self.result_label.config(text="Now charging load optimized hours")

    def price_optimized_charge(self):
        self.price_optimized = True
        self.result_label.config(text="Now charging price optimized hours")
        
    def price_and_load_optimized_charge(self):
        self.price_optimized = True
        self.load_optimized = True
        self.result_label.config(text="Now charging both load and price optimized hours")

    def control_charging(self):
        
        if self.battery_percentage > 80:
            self.stop_all_charging() 
        elif self.load_optimized and not self.price_optimized:
            if self.sim_time_hour in self.load_optimized_hours:
                self.start_charge() #could add a flag to check if it already is on       
            else:
                self.stop_charge()
        elif self.price_optimized and not self.load_optimized:
            if self.sim_time_hour in self.price_optimized_hours:
                self.should_charge() # again add flag ?
            else:
                self.stop_charge()
        elif self.price_optimized and self.load_optimized:
            if self.sim_time_hour in self.price_optimized_hours and self.sim_time_hour in self.load_optimized_hours:
                self.start_charge()
            else:
                self.stop_charge()
        


    def start_charging(self):
        self.start_charge_request()

    def stop_charging(self):
        self.stop_charge_request()
        
    def discharge_battery(self):
        self.stop_all_charging()
        self.discharge_battery_request()
        self.result_label.config(text="Discharged battery, stopped all charging.")
        
    def stop_all_charging(self):
        self.result_label.config(text="Stopped charging")
        self.stop_charge_request()
        self.should_charge = False
        self.load_optimized = False
        self.price_optimized = False

    def start_charge_request(self):
        requests.post(f"{BASE_URL}/charge", json={"charging": "on"}, headers={"Content-Type": "application/json"})

    def stop_charge_request(self):
        requests.post(f"{BASE_URL}/charge", json={"charging": "off"}, headers={"Content-Type": "application/json"})

    def discharge_battery_request(self):
        requests.post(f"{BASE_URL}/discharge", json={"discharging": "on"}, headers={"Content-Type": "application/json"})


def main():
    root = tk.Tk()
    app = EVChargeControllerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()






