import customtkinter as ctk
from tkinter import *
from CTkMessagebox import CTkMessagebox
import datetime
import json
import time

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"  # Removing default pygame module messages

import pygame


class DuplicateError(Exception):
    pass


class AlarmError(Exception):
    pass


class AlarmClock(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("My Alarm Clock")
        self.font = ("sans-serif", 13, "bold")
        self.resizable(0, 0)  # Disables maximise button

        ctk.set_appearance_mode("Dark")

        self.curr_time = datetime.datetime.now().strftime("%H:%M:%S %p")

        # Row 0
        self.clock_label = ctk.CTkLabel(self, text="CURRENT TIME")
        self.clock_label.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        self.alarm_lst_lbl = ctk.CTkLabel(self, text="YOUR ALARM LIST")
        self.alarm_lst_lbl.grid(row=0, column=2, columnspan=2, padx=10, pady=10)

        # Row 1
        self.frame1 = ctk.CTkFrame(self)
        self.frame1.grid(row=1, column=0,  columnspan=2, padx=20, pady=10)
        self.time = ctk.CTkLabel(self.frame1, text=self.curr_time, padx=0, font=("arial", 50, "bold"))
        self.time.pack()

        self.alarm_lst = Listbox(self, width=25, selectmode=SINGLE)
        self.alarm_lst.grid(row=1, column=2, columnspan=2, padx=20, pady=10)

        # Row 2
        self.hr_label = ctk.CTkLabel(self, text="ENTER HOUR: ")
        self.hr_label.grid(row=2, column=0, padx=10)

        self.min_label = ctk.CTkLabel(self, text="ENTER MINUTE: ")
        self.min_label.grid(row=2, column=1, padx=10)

        self.del_button = ctk.CTkButton(self, text="DELETE ALARM", command=self.del_alarm, fg_color="#DD1111",
                                        hover_color="#C40E0E")
        self.del_button.grid(row=2, column=2, columnspan=2, padx=10, pady=20, rowspan=2)

        # Row 3
        self.hr_entry_box = ctk.CTkEntry(self, width=50)
        self.hr_entry_box.grid(row=3, column=0)
        self.hr_entry_box.focus_set()

        self.min_entry_box = ctk.CTkEntry(self, width=50)
        self.min_entry_box.grid(row=3, column=1)

        self.del_all_btn = ctk.CTkButton(self, text="DELETE ALL ALARMS", command=self.delete_all_alarms, fg_color="#DA0909"
                                         , hover_color="#B30707")
        self.del_all_btn.grid(row=3, column=2, columnspan=2, padx=10, pady=20, rowspan=2)

        # Row 4
        self.add_button = ctk.CTkButton(self, text="ADD ALARM", command=self.add_alarm, width=290)
        self.add_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

        self.load_list_of_alarms()

        self.bind("<Return>", lambda event: self.add_alarm())  # For inserting item using Enter

    def clock(self):
        cur_datetime = datetime.datetime.now().strftime("%H:%M:%S %p")
        self.time.configure(text=cur_datetime)
        set_alarm = self.get_alarm()
        cur_hr_min = datetime.datetime.now().strftime("%H:%M %p")
        if set_alarm is not None:
            if set_alarm == cur_hr_min:
                self.del_data_in_json(cur_hr_min)
                self.sort_data_in_json()
                self.load_list_of_alarms()
                self.play_music()
                time.sleep(2)
                icon = CTkMessagebox(self, title="Alarm", message=f"Alarm for {set_alarm}!!!")
                self.pause_music()

            elif set_alarm < cur_hr_min:
                self.del_data_in_json(set_alarm)
                self.sort_data_in_json()
                self.load_list_of_alarms()
        self.time.after(1000, self.clock)

    def get_alarm(self):
        try:
            alarms = self.get_list_of_alarms()
            assert len(alarms) != 0
        except AssertionError:
            pass
        else:
            return alarms[0]

    def del_alarm(self):
        try:
            selected_items = self.alarm_lst.curselection()
            assert len(selected_items) != 0
        except AssertionError:
            icon = CTkMessagebox(title="SELECTION ERROR", message="PLEASE SELECT AN ITEM!", icon="cancel")
        else:
            time_to_delete = self.alarm_lst.get(selected_items[0])
            self.alarm_lst.delete(selected_items[0])
            self.del_data_in_json(time_to_delete)
            self.sort_data_in_json()

    def add_alarm(self):
        try:
            hr = self.hr_entry_box.get()
            min = self.min_entry_box.get()
            assert hr != "" and min != ""
            assert hr.isnumeric() is True and min.isnumeric() is True
            assert 0 <= int(hr) <= 23 and 0 <= int(min) <= 59
            data = self.load_json_file()
            date_obj = datetime.datetime.strptime(hr + ":" + min, "%H:%M")
            alarm_slot = date_obj.strftime("%H:%M %p")
            for i in data:
                if data[i] == alarm_slot:
                    raise DuplicateError

        except AssertionError:
            icon = CTkMessagebox(title="ERROR", message="Invalid timeslot", icon="cancel")
        except DuplicateError:
            icon = CTkMessagebox(title="ERROR", message="Alarm already exists", icon="cancel")
        else:
            data["total_alarms"] += 1
            data.update({str(data["total_alarms"]): alarm_slot})
            self.write_to_json_file(data)
            self.hr_entry_box.delete(0, END)
            self.min_entry_box.delete(0, END)
            self.load_list_of_alarms()

    def get_list_of_alarms(self):
        data = self.load_json_file()
        lst_of_alarms = []
        for i in data:
            if i.isdigit() is True:
                lst_of_alarms.append(data[i])
        return sorted(lst_of_alarms)

    def load_list_of_alarms(self):
        lst = sorted(self.get_list_of_alarms())
        self.alarm_lst.delete(0, END)
        self.alarm_lst.insert(END, *lst)

    def delete_all_alarms(self):
        icon = CTkMessagebox(title="Confirmation", message="Do you want to delete all alarms in your list?",
                             icon="question", option_1="No", option_2="Yes")
        if icon.get() == "Yes":
            self.alarm_lst.delete(0, END)
            data = self.load_json_file()
            updated_data = {key: value for (key, value) in data.items() if key.isdigit() is False}
            updated_data["total_alarms"] = 1
            self.write_to_json_file(updated_data)

    def sort_data_in_json(self):
        data = self.load_json_file()
        lst_of_alarms = self.get_list_of_alarms()  # Loading only the alarms (timeslots) from the json file.
        lst_of_alarms.sort()  # Sorting the list of alarms(timeslots).
        updated_data = {key: value for (key, value) in data.items() if key.isdigit() is False}
        # Removing all data that has a key of number string. That data will be the timeslots associated.
        # So, in the end, only the total_alarms and Example_Alarm will remain in the json file.
        for index, value in enumerate(lst_of_alarms, 1):
            updated_data.update({str(index): value, })
        self.write_to_json_file(updated_data)

    def del_data_in_json(self, time_to_delete):
        data = self.load_json_file()
        data["total_alarms"] -= 1  # Subtracting from total alarm count
        # JSON data keeps data types intact, so we subtract without type conversion
        data = {key: value for (key,value) in data.items() if value != time_to_delete}
        self.write_to_json_file(data)



    @staticmethod
    def load_json_file():
        with open("file.json", "r") as json_file:
            data = json.load(json_file)
            return data

    @staticmethod
    def write_to_json_file(data):
        with open("file.json", "w") as json_file:
            json.dump(data, json_file, indent=4)

    @staticmethod
    def play_music():
        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.init()
        pygame.mixer.init()
        pygame.mixer.music.load("bird_alarm.mp3")
        pygame.mixer.music.play()

    @staticmethod
    def pause_music():
        pygame.mixer.music.pause()


x = AlarmClock()
x.clock()
x.mainloop()
