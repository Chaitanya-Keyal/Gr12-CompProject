import copy
import random
import threading
import tkinter as tk
import tkinter.ttk as ttk
from time import sleep
from tkinter import messagebox as msgb
import os
from PIL import Image, ImageOps, ImageTk

from client_framework import Client
from http_wrapper import Http

try:
    from musicplayer import play as music
except:
    print("No Output Devices Found")

ASSET = "/Assets/Mnply_Assets"
ASSET = ASSET if os.path.exists(ASSET) else "Client/" + ASSET


class Property:
    def __init__(self, details):
        self.name = details[0]
        self.position = details[1]
        self.colour = details[2]
        self.hex = details[3]
        self.price = details[4]
        self.rent_values = [
            details[5],
            details[6],
            details[7],
            details[8],
            details[9],
            details[10],
            details[11],
        ]
        self.mortgage = details[12]
        self.build = details[13]

        self.owner = None
        self.houses = -1
        self.isMortgaged = False
        """
        No. of houses meaning:
        -1 : Rent
        0 : Rent with colour set
        1: Rent with 1 house
        2: Rent with 2 houses
        3: Rent with 3 houses
        4: Rent with 4 houses
        5: Rent with hotel
        """

    def rent(self):
        if self.rent_values[self.houses + 1]:
            return self.rent_values[self.houses + 1]
        elif self.colour == "Station":
            return
        elif self.colour == "Utility":
            return
        else:
            print("Rent Error")

    def value(self):
        val = self.price
        if 1 <= self.houses <= 5:
            val += self.houses * self.build

        return val


class Monopoly(tk.Toplevel):
    def __init__(self, playerdetails, me, send, hobj: Http):
        super().__init__()
        self.player_details = playerdetails
        self.me = me
        Monopoly.hobj = hobj
        print(self.player_details[self.me])
        self.send_msg = send
        self.create_window()
        self.create_gui_divisions()
        self.initialise()
        self.create_image_obj()
        self.dice_tokens()
        self.action_frame_popup("Default")
        self.player_frame_popup()
        for i in self.player_details:
            self.move(i, 0)

    def initialise(self):
        self.property_frame = tk.Frame()
        self.property_frame.destroy()
        self.end_button = ttk.Button()
        self.end_button.destroy()
        self.buy_button = ttk.Button()
        self.buy_button.destroy()
        self.mortgage_button = ttk.Button()
        self.mortgage_button.destroy()
        self.trade_button = ttk.Button()
        self.trade_button.destroy()
        self.build_button = ttk.Button()
        self.build_button.destroy()
        self.property_pos_displayed = None
        self.current_txt = "Default"
        self.board_canvas.bind("<Button-1>", self.click_to_position)
        self.uuids = list(self.player_details.keys())
        self.turn = self.uuids[0]
        self.doubles_counter = 0
        self.properties = {}
        details = self.hobj.mply_details()
        for i in range(40):
            self.properties[i] = Property(details[i])

        for i in self.player_details:
            self.player_details[i].update(
                {"Money": 1500, "Injail": False, "Position": 0, "Properties": []}
            )  # Properties will store obj from properties dict

        cli_thread = threading.Thread(target=self.CLI)
        cli_thread.start()

    def updater(self, msg):
        if msg[1] == "ROLL":
            self.roll_dice(msg[2], True)
        elif msg[1] == "BUY":
            self.buy_property(msg[2], msg[0], True)
        elif msg[1] == "BUILD":
            self.build(msg[2], msg[3], True)
        elif msg[1] == "END":
            self.end_turn(True)

    def create_window(self):
        screen_width = int(0.9 * self.winfo_screenwidth())
        screen_height = int(screen_width / 1.9)
        x_coord = self.winfo_screenwidth() // 2 - screen_width // 2
        y_coord = (self.winfo_screenheight() - 70) // 2 - screen_height // 2

        self.board_side = int(screen_height * 0.9)  # Length of board
        self.property_width = self.board_side / 12.2  # Width of one property on board
        self.property_height = self.property_width * 1.6
        self.token_width = int(self.property_height * 0.176)

        self.title("Monopoly")
        self.resizable(False, False)
        self.geometry(f"{screen_width}x{screen_height}+{x_coord}+{y_coord}")
        self.config(bg="white")
        # self.protocol("WM_DELETE_WINDOW", self.winfo_parent.destroy)

    def create_gui_divisions(self):
        self.board_canvas = tk.Canvas(
            self, width=self.board_side, height=self.board_side
        )
        self.board_canvas.place(relx=0.01, rely=0.04, anchor="nw")

        self.main_frame = tk.Frame(
            self,
            width=self.board_side - 2,
            height=self.board_side - 2,
            background="white",
        )
        self.main_frame.place(relx=0.99, rely=0.04, anchor="ne")

    def create_image_obj(self):
        self.board_image = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/BoardIMG.jpg").resize(
                    (self.board_side, self.board_side), Image.Resampling.LANCZOS
                )
            )
        )
        self.board_canvas.create_image(2, 2, image=self.board_image, anchor="nw")

        self.info_tag = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/Info/big_info.png").resize(
                    (int(self.property_width / 2), int(self.property_width / 2)),
                    Image.Resampling.LANCZOS,
                )
            )
        )

        self.station_image = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/station.png").resize(
                    (int(2.5 * self.property_width), int(2.5 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )

        self.water_image = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/water.png").resize(
                    (int(2.5 * self.property_width), int(2 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )

        self.electric_image = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/electric.png").resize(
                    (int(2 * self.property_width), int(2.25 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )

        self.dice1 = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/Die/dice1.png").resize(
                    (int(0.9 * self.property_width), int(0.9 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )
        self.dice2 = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/Die/dice2.png").resize(
                    (int(0.9 * self.property_width), int(0.9 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )
        self.dice3 = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/Die/dice3.png").resize(
                    (int(0.9 * self.property_width), int(0.9 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )
        self.dice4 = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/Die/dice4.png").resize(
                    (int(0.9 * self.property_width), int(0.9 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )
        self.dice5 = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/Die/dice5.png").resize(
                    (int(0.9 * self.property_width), int(0.9 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )
        self.dice6 = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/Die/dice6.png").resize(
                    (int(0.9 * self.property_width), int(0.9 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )

        self.red_token_image = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/Tokens/red.png").resize(
                    (self.token_width, self.token_width),
                    Image.Resampling.LANCZOS,
                )
            )
        )
        self.green_token_image = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/Tokens/green.png").resize(
                    (self.token_width, self.token_width),
                    Image.Resampling.LANCZOS,
                )
            )
        )
        self.blue_token_image = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/Tokens/blue.png").resize(
                    (self.token_width, self.token_width),
                    Image.Resampling.LANCZOS,
                )
            )
        )
        self.yellow_token_image = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/Tokens/yellow.png").resize(
                    (self.token_width, self.token_width),
                    Image.Resampling.LANCZOS,
                )
            )
        )
        self.mr_monopoly = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/mr_monopoly.png").resize(
                    (
                        int((self.board_side - 2) // 2.05),
                        int((self.board_side - 2) // 1.75),
                    ),
                    Image.Resampling.LANCZOS,
                )
            )
        )
        self.mr_monopoly_frame = tk.Frame(
            self.main_frame,
            width=(self.board_side - 2) // 2.05,
            height=(self.board_side - 2) // 1.75,
            bg="#F9FBFF",
            highlightthickness=0,
            highlightbackground="#F9FBFF",
        )

        self.mr_monopoly_frame.place(relx=1, rely=1, anchor="se")
        tk.Label(
            self.mr_monopoly_frame,
            image=self.mr_monopoly,
            border=0,
            highlightthickness=0,
            bg="#FFFFFF",
        ).pack()

        self.house_images = []

    def dice_tokens(self):
        self.die_dict = dict(
            zip(
                (1, 2, 3, 4, 5, 6),
                (
                    self.dice1,
                    self.dice2,
                    self.dice3,
                    self.dice4,
                    self.dice5,
                    self.dice6,
                ),
            )
        )

        button_style = ttk.Style()
        button_style.configure(
            "my.TButton", font=("times", int(self.property_width / 3))
        )

        self.roll_button = ttk.Button(
            self.board_canvas,
            text="Roll Dice",
            style="my.TButton",
            command=self.roll_dice,
        )
        self.roll_button.place(relx=0.5, rely=0.5, anchor="center")

        if self.turn != self.me:
            self.roll_button.configure(state="disabled")

        self.dice_spot1 = tk.Label(
            self.board_canvas, image=self.dice5, border=0, highlightthickness=0
        )
        self.dice_spot1.place(relx=0.485, rely=0.46, anchor="se")

        self.dice_spot2 = tk.Label(
            self.board_canvas, image=self.dice5, border=0, highlightthickness=0
        )
        self.dice_spot2.place(relx=0.515, rely=0.46, anchor="sw")

        self.red_token = tk.Button(
            self.board_canvas,
            image=self.red_token_image,
            border=0,
            highlightthickness=0,
            command=lambda: self.open_children("red"),
        )

        self.green_token = tk.Button(
            self.board_canvas,
            image=self.green_token_image,
            border=0,
            highlightthickness=0,
            command=lambda: self.open_children("green"),
        )

        self.blue_token = tk.Button(
            self.board_canvas,
            image=self.blue_token_image,
            border=0,
            highlightthickness=0,
            command=lambda: self.open_children("blue"),
        )

        self.yellow_token = tk.Button(
            self.board_canvas,
            image=self.yellow_token_image,
            border=0,
            highlightthickness=0,
            command=lambda: self.open_children("gold"),
        )

    def count_colour(self, propertypos):
        owner = self.properties[propertypos].owner
        if owner:
            colour = self.properties[propertypos].colour
            c = 0
            for i in self.player_details[owner]["Properties"]:
                if i.colour == colour:
                    c += 1
            return c
        else:
            return None

    def owner_detail(self, propertypos, s="Name"):
        return self.player_details[self.properties[propertypos].owner][s]

    def update_game(self, action_frame_text=None):
        if self.property_frame.winfo_exists():
            self.property_frame.destroy()
            self.property_frame_popup(self.property_pos_displayed)
        l = []
        for i in self.player_details:
            if self.player_tree.item(i, "open"):
                l.append(i)
        self.player_tree.destroy()
        self.player_frame_popup(l)
        self.house_images = []
        self.place_houses()
        self.action_frame.destroy()
        if action_frame_text:
            self.action_frame_popup(action_frame_text)
        else:
            self.action_frame_popup(self.current_txt)
        if self.turn != self.me:
            self.roll_button.configure(state="disabled")

    # region # Property Frame

    def station_property_frame(self, position):
        station_label = tk.Label(
            self.property_frame,
            image=self.station_image,
            border=0,
            highlightthickness=0,
        )
        station_label.place(relx=0.5, rely=0.2, anchor="center")

        tk.Label(
            self.property_frame,
            text=self.properties[position].name.upper(),
            font=("times", (self.board_side - 2) // 40),
            bg="#F9FBFF",
        ).place(relx=0.5, rely=0.4, anchor="center")

        tk.Button(
            self.property_frame,
            text="✕",
            font=("courier", (self.board_side - 2) // 60),
            bg="#F9FBFF",
            highlightthickness=0,
            border=0,
            activebackground="#F9FBFF",
            command=self.property_frame.destroy,
        ).place(relx=0.95, rely=0.05, anchor="ne")

        canvas = tk.Canvas(
            self.property_frame,
            highlightthickness=0,
            width=(self.board_side - 2) // 2.25,
            height=(self.board_side - 2) // 3.2,
            bg="#F9FBFF",
        )
        canvas.place(relx=0.5, rely=0.7, anchor="center")
        canvas.update()
        y_coord = canvas.winfo_height() / 12

        ttk.Separator(canvas, orient="horizontal").place(
            relx=0.5, rely=0.85, anchor="center", relwidth=0.8
        )
        ttk.Separator(canvas, orient="horizontal").place(
            relx=0.5, rely=0.15, anchor="center", relwidth=0.8
        )

        tk.Button(
            self.property_frame,
            image=self.info_tag,
            border=0,
            highlightthickness=0,
            command=lambda: self.show_message(
                "Station Rules", "Station Rules", timeout=2000
            ),
        ).place(x=35, rely=0.925, anchor="center")

        row_counter = 0
        stations_data = {
            "Unowned; Buy For": self.properties[position].price,
            "Rent": 25,
            "If 2 Stations are owned": 50,
            "If 3 Stations are owned": 100,
            "If 4 Stations are owned": 200,
        }
        for (
            i,
            j,
        ) in stations_data.items():  # Placing and formatting Rent data on card
            row_counter += 1
            try:
                if row_counter == self.count_colour(position) + 1:
                    canvas.create_text(
                        2,
                        y_coord - 2,
                        anchor="w",
                        text="▶",
                        font=("times", (self.board_side - 2) // 32),
                        fill=self.owner_detail(position, "Colour"),
                    )
            except:
                pass
            if row_counter == 1:
                if self.properties[position].owner:
                    canvas.create_text(
                        canvas.winfo_width() / 2,
                        y_coord,
                        anchor="center",
                        text=f"Owner: {self.owner_detail(position,'Name')}",
                        font=("times", (self.board_side - 2) // 45),
                        fill=self.owner_detail(position, "Colour"),
                    )
                else:
                    canvas.create_text(
                        2,
                        y_coord - 2,
                        anchor="w",
                        text="▶",
                        font=("times", (self.board_side - 2) // 32),
                    )
                    canvas.create_text(
                        25,
                        y_coord,
                        anchor="w",
                        text=i,
                        font=("times", (self.board_side - 2) // 45),
                    )
                    canvas.create_text(
                        canvas.winfo_width() / 1.3,
                        y_coord,
                        text="₩",
                        angle=180,
                        font=("courier", (self.board_side - 2) // 45),
                    )
                    canvas.create_text(
                        canvas.winfo_width() - 25,
                        y_coord,
                        anchor="e",
                        text=str(j),
                        font=("times", (self.board_side - 2) // 45),
                    )
            else:
                canvas.create_text(
                    25,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (self.board_side - 2) // 45),
                )
                canvas.create_text(
                    canvas.winfo_width() / 1.3,
                    y_coord,
                    text="₩",
                    angle=180,
                    font=("courier", (self.board_side - 2) // 45),
                )
                canvas.create_text(
                    canvas.winfo_width() - 25,
                    y_coord,
                    anchor="e",
                    text=str(j),
                    font=("times", (self.board_side - 2) // 45),
                )

            y_coord += canvas.winfo_height() / 6
        canvas.create_text(
            45,
            y_coord,
            anchor="w",
            text="Mortgage Value",
            font=("times", (self.board_side - 2) // 51),
        )
        canvas.create_text(
            canvas.winfo_width() / 1.3,
            y_coord,
            text="₩",
            angle=180,
            font=("courier", (self.board_side - 2) // 51),
        )
        canvas.create_text(
            canvas.winfo_width() - 35,
            y_coord,
            anchor="e",
            text=self.properties[position].mortgage,
            font=("times", (self.board_side - 2) // 51),
        )

    def utility_property_frame(self, position):
        if position == 28:
            utility_image = self.water_image
        else:
            utility_image = self.electric_image
        utility_label = tk.Label(
            self.property_frame, image=utility_image, border=0, highlightthickness=0
        )
        utility_label.place(relx=0.5, rely=0.2, anchor="center")

        tk.Label(
            self.property_frame,
            text=self.properties[position].name.upper(),
            font=("times", (self.board_side - 2) // 40),
            bg="#F9FBFF",
        ).place(relx=0.5, rely=0.4, anchor="center")

        tk.Button(
            self.property_frame,
            text="✕",
            font=("courier", (self.board_side - 2) // 60),
            bg="#F9FBFF",
            highlightthickness=0,
            border=0,
            activebackground="#F9FBFF",
            command=self.property_frame.destroy,
        ).place(relx=0.95, rely=0.05, anchor="ne")

        canvas = tk.Canvas(
            self.property_frame,
            highlightthickness=0,
            width=(self.board_side - 2) // 2.25,
            height=(self.board_side - 2) // 3.2,
            bg="#F9FBFF",
        )
        canvas.place(relx=0.5, rely=0.7, anchor="center")
        canvas.update()
        y_coord = canvas.winfo_height() / 14

        ttk.Separator(canvas, orient="horizontal").place(
            relx=0.5, rely=0.85, anchor="center", relwidth=0.8
        )

        ttk.Separator(canvas, orient="horizontal").place(
            relx=0.5, rely=0.15, anchor="center", relwidth=0.8
        )

        tk.Button(
            self.property_frame,
            image=self.info_tag,
            border=0,
            highlightthickness=0,
            command=lambda: self.show_message(
                "Utility Rules", "Utility Rules", timeout=2000
            ),
        ).place(x=35, rely=0.925, anchor="center")

        row_counter = 0
        try:  # if dice has been rolled
            utilities_data = {
                "Unowned; Buy For": self.properties[position].price,
                f"Rent based on last roll ({self.current_move}),": None,
                "If 1 utility is owned:": None,
                f" 4   x  {self.current_move}     = ": 4 * self.current_move,
                "If 2 utilities are owned:": None,
                f"10  x  {self.current_move}     =": 10 * self.current_move,
            }
        except:  # if dice has not been rolled yet
            utilities_data = {
                "Unowned; Buy For": self.properties[position].price,
                "Rent based on roll (10),": None,
                "If 1 utility is owned:": None,
                f" 4   x  10     = ": 40,
                "If 2 utilities are owned:": None,
                f"10  x  10     =": 100,
            }
        for (
            i,
            j,
        ) in utilities_data.items():  # Placing and formatting Rent data on card
            row_counter += 1
            try:
                if row_counter == self.count_colour(position) * 2 + 1:
                    canvas.create_text(
                        2,
                        y_coord - 2,
                        anchor="w",
                        text="▶",
                        font=("times", (self.board_side - 2) // 32),
                        fill=self.owner_detail(position, "Colour"),
                    )
            except:
                pass
            if row_counter == 1:
                if self.properties[position].owner:
                    canvas.create_text(
                        canvas.winfo_width() / 2,
                        y_coord,
                        anchor="center",
                        text=f"Owner: {self.owner_detail(position,'Name')}",
                        font=("times", (self.board_side - 2) // 45),
                        fill=self.owner_detail(position, "Colour"),
                    )
                else:
                    canvas.create_text(
                        2,
                        y_coord - 2,
                        anchor="w",
                        text="▶",
                        font=("times", (self.board_side - 2) // 32),
                    )
                    canvas.create_text(
                        25,
                        y_coord,
                        anchor="w",
                        text=i,
                        font=("times", (self.board_side - 2) // 45),
                    )
                    canvas.create_text(
                        canvas.winfo_width() / 1.3,
                        y_coord,
                        text="₩",
                        angle=180,
                        font=("courier", (self.board_side - 2) // 45),
                    )
                    canvas.create_text(
                        canvas.winfo_width() - 25,
                        y_coord,
                        anchor="e",
                        text=str(j),
                        font=("times", (self.board_side - 2) // 45),
                    )
            elif row_counter in [2, 3, 5]:  # text row
                canvas.create_text(
                    25,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (self.board_side - 2) // 45),
                )
            elif row_counter in [4, 6]:  # rent row
                canvas.create_text(
                    canvas.winfo_width() / 2.75,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (self.board_side - 2) // 45),
                )
                canvas.create_text(
                    canvas.winfo_width() / 1.3,
                    y_coord,
                    text="₩",
                    angle=180,
                    font=("courier", (self.board_side - 2) // 45),
                )
                canvas.create_text(
                    canvas.winfo_width() - 25,
                    y_coord,
                    anchor="e",
                    text=str(j),
                    font=("times", (self.board_side - 2) // 45),
                )

            y_coord += canvas.winfo_height() / 7
        canvas.create_text(
            45,
            y_coord,
            anchor="w",
            text="Mortgage Value",
            font=("times", (self.board_side - 2) // 51),
        )
        canvas.create_text(
            canvas.winfo_width() / 1.3,
            y_coord,
            text="₩",
            angle=180,
            font=("courier", (self.board_side - 2) // 51),
        )
        canvas.create_text(
            canvas.winfo_width() - 35,
            y_coord,
            anchor="e",
            text=self.properties[position].mortgage,
            font=("times", (self.board_side - 2) // 51),
        )

    def colour_property_frame(self, position):
        title_frame = tk.Frame(
            self.property_frame,
            width=(self.board_side - 2) // 2.25,
            height=(self.board_side - 2) // 10,
            bg=self.properties[position].hex,
            highlightthickness=2,
            highlightbackground="black",
        )
        title_frame.place(relx=0.5, rely=0.125, anchor="center")

        tk.Label(
            title_frame,
            text="TITLE DEED",
            font=("times", (self.board_side - 2) // 56),
            bg=self.properties[position].hex,
        ).place(relx=0.5, rely=0.25, anchor="center")

        tk.Label(
            title_frame,
            text=self.properties[position].name.upper(),
            font=("times", (self.board_side - 2) // 42),
            bg=self.properties[position].hex,
        ).place(relx=0.5, rely=0.65, anchor="center")

        tk.Button(
            title_frame,
            text="✕",
            font=("courier", (self.board_side - 2) // 60),
            bg=self.properties[position].hex,
            highlightthickness=0,
            border=0,
            activebackground=self.properties[position].hex,
            command=self.property_frame.destroy,
        ).place(relx=1, rely=0, anchor="ne")

        canvas = tk.Canvas(
            self.property_frame,
            highlightthickness=0,
            width=(self.board_side - 2) // 2.25,
            height=(self.board_side - 2) // 2.3,
            bg="#F9FBFF",
        )
        canvas.place(relx=0.5, rely=0.6, anchor="center")
        canvas.update()
        y_coord = canvas.winfo_height() / 23

        ttk.Separator(canvas, orient="horizontal").place(
            relx=0.5, rely=0.725, anchor="center", relwidth=0.8
        )

        ttk.Separator(canvas, orient="horizontal").place(
            relx=0.5, rely=0.09, anchor="center", relwidth=0.8
        )

        tk.Button(
            self.property_frame,
            image=self.info_tag,
            border=0,
            highlightthickness=0,
            command=lambda: self.show_message(
                "Hotel Rules", "Hotel Rules", timeout=2000
            ),
        ).place(x=35, rely=0.9, anchor="center")

        vals = [self.properties[position].price]
        vals.extend(self.properties[position].rent_values)
        vals.extend(
            [
                self.properties[position].mortgage,
                self.properties[position].build,
                self.properties[position].build,
            ]
        )
        d = dict(
            zip(
                [
                    "Unowned; Buy For",
                    "Rent",
                    "With Color Set",
                    "With 1 House",
                    "With 2 Houses",
                    "With 3 Houses",
                    "With 4 Houses",
                    "With Hotel",
                    "Mortgage Value",
                    "House Cost",
                    "Hotel Cost",
                ],
                vals,
            )
        )

        row_counter = -3
        for i, j in d.items():  # Placing and formatting Rent data on card
            row_counter += 1
            try:
                if row_counter == self.properties[position].houses:
                    canvas.create_text(
                        2,
                        y_coord - 2,
                        anchor="w",
                        text="▶",
                        font=("times", (self.board_side - 2) // 32),
                        fill=self.owner_detail(position, "Colour"),
                    )
            except:
                pass

            if row_counter == -2:
                if self.properties[position].owner:
                    canvas.create_text(
                        canvas.winfo_width() / 2,
                        y_coord,
                        anchor="center",
                        text=f"Owner: {self.owner_detail(position,'Name')}",
                        font=("times", (self.board_side - 2) // 45),
                        fill=self.owner_detail(position, "Colour"),
                    )
                else:
                    canvas.create_text(
                        2,
                        y_coord - 2,
                        anchor="w",
                        text="▶",
                        font=("times", (self.board_side - 2) // 32),
                    )
                    canvas.create_text(
                        25,
                        y_coord,
                        anchor="w",
                        text=i,
                        font=("times", (self.board_side - 2) // 45),
                    )
                    canvas.create_text(
                        canvas.winfo_width() / 1.375,
                        y_coord,
                        text="₩",
                        angle=180,
                        font=("courier", (self.board_side - 2) // 45),
                    )
                    canvas.create_text(
                        canvas.winfo_width() - 25,
                        y_coord,
                        anchor="e",
                        text=str(j),
                        font=("times", (self.board_side - 2) // 45),
                    )
            if row_counter in [-1, 0]:  # rent, double rent
                canvas.create_text(
                    25,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (self.board_side - 2) // 42),
                )
                canvas.create_text(
                    canvas.winfo_width() / 1.375,
                    y_coord,
                    text="₩",
                    angle=180,
                    font=("courier", (self.board_side - 2) // 42),
                )
                canvas.create_text(
                    canvas.winfo_width() - 25,
                    y_coord,
                    anchor="e",
                    text=str(j),
                    font=("times", (self.board_side - 2) // 42),
                )
            elif row_counter in [1, 2, 3, 4]:  # houses
                canvas.create_text(
                    25,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (self.board_side - 2) // 42),
                    fill="green",
                )
                canvas.create_text(
                    canvas.winfo_width() / 1.375,
                    y_coord,
                    text="₩",
                    angle=180,
                    font=("courier", (self.board_side - 2) // 42),
                    fill="green",
                )
                canvas.create_text(
                    canvas.winfo_width() - 25,
                    y_coord,
                    anchor="e",
                    text=str(j),
                    font=("times", (self.board_side - 2) // 42),
                    fill="green",
                )
            elif row_counter == 5:  # hotel
                canvas.create_text(
                    25,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (self.board_side - 2) // 42),
                    fill="red",
                )
                canvas.create_text(
                    canvas.winfo_width() / 1.375,
                    y_coord,
                    text="₩",
                    angle=180,
                    font=("courier", (self.board_side - 2) // 42),
                    fill="red",
                )
                canvas.create_text(
                    canvas.winfo_width() - 25,
                    y_coord,
                    anchor="e",
                    text=str(j),
                    font=("times", (self.board_side - 2) // 42),
                    fill="red",
                )
            elif row_counter == 6:  # mortgage
                canvas.create_text(
                    45,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (self.board_side - 2) // 49),
                )
                canvas.create_text(
                    canvas.winfo_width() / 1.375,
                    y_coord,
                    text="₩",
                    angle=180,
                    font=("courier", (self.board_side - 2) // 49),
                )
                canvas.create_text(
                    canvas.winfo_width() - 35,
                    y_coord,
                    anchor="e",
                    text=str(j),
                    font=("times", (self.board_side - 2) // 49),
                )
            elif row_counter == 7:  # build house
                canvas.create_text(
                    45,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (self.board_side - 2) // 49),
                    fill="green",
                )
                canvas.create_text(
                    canvas.winfo_width() / 1.375,
                    y_coord,
                    text="₩",
                    angle=180,
                    font=("courier", (self.board_side - 2) // 49),
                    fill="green",
                )
                canvas.create_text(
                    canvas.winfo_width() - 35,
                    y_coord,
                    anchor="e",
                    text=str(j),
                    font=("times", (self.board_side - 2) // 49),
                    fill="green",
                )
            elif row_counter == 8:  # build hotel
                canvas.create_text(
                    45,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (self.board_side - 2) // 49),
                    fill="red",
                )
                canvas.create_text(
                    canvas.winfo_width() / 1.375,
                    y_coord,
                    text="₩",
                    angle=180,
                    font=("courier", (self.board_side - 2) // 49),
                    fill="red",
                )
                canvas.create_text(
                    canvas.winfo_width() - 35,
                    y_coord,
                    anchor="e",
                    text=str(j),
                    font=("times", (self.board_side - 2) // 49),
                    fill="red",
                )

            y_coord += canvas.winfo_height() / 11

    def property_frame_popup(self, position):
        position %= 40
        if self.property_frame.winfo_exists():
            self.property_frame.destroy()
        self.property_pos_displayed = position
        self.property_frame = tk.Frame(
            self.main_frame,
            width=(self.board_side - 2) // 2.05,
            height=(self.board_side - 2) // 1.75,
            bg="#F9FBFF",
            highlightthickness=2,
            highlightbackground="black",
        )

        self.property_frame.place(relx=1, rely=1, anchor="se")

        if position in [5, 15, 25, 35]:
            self.station_property_frame(position)
        elif position in [12, 28]:
            self.utility_property_frame(position)
        else:
            self.colour_property_frame(position)

    # endregion

    # region # Player Frame

    def player_frame_popup(
        self, list_of_open=[]
    ):  # TODO: Highlight me, Adjust row height
        self.player_frame = tk.Frame(
            self.main_frame,
            width=(self.board_side - 2) // 2.05,
            height=(self.board_side - 2) // 1.75,
        )

        self.player_frame.place(relx=0, rely=1, anchor="sw")

        scroll = ttk.Scrollbar(self.player_frame, orient="vertical")
        scroll.place(relx=1, rely=0, relwidth=0.05, anchor="ne", relheight=1)

        self.player_tree = ttk.Treeview(
            self.player_frame, columns=("Player", "Value"), yscrollcommand=scroll.set
        )

        scroll.configure(command=self.player_tree.yview)

        self.player_tree.column(
            "#0",
            width=10,
        )
        self.player_tree.column(
            "Player",
            width=int((self.board_side - 2) // 4.25) - 10,
            anchor="center",
            minwidth=int((self.board_side - 2) // 4.7),
        )
        self.player_tree.column(
            "Value",
            width=int((self.board_side - 2) // 4.25) - 10,
            anchor="center",
            minwidth=int((self.board_side - 2) // 4.7),
        )
        self.player_tree.heading("#0", text="")
        self.player_tree.heading("Player", text="Player → Properties", anchor="center")
        self.player_tree.heading("Value", text="Cash → Value", anchor="center")

        for i, j in self.player_details.items():
            if i == self.me:
                self.player_tree.insert(
                    parent="",
                    index="end",
                    iid=i,
                    text="",
                    values=(j["Name"], j["Money"]),
                    tags=("me"),
                )

            else:
                self.player_tree.insert(
                    parent="",
                    index="end",
                    iid=i,
                    text="",
                    values=(j["Name"], j["Money"]),
                )
            self.player_tree.tag_configure(
                "me", background=self.player_details[self.me]["Colour"]
            )
            if i in list_of_open:
                self.player_tree.item(i, open=True)
            count = 0
            for k in j["Properties"]:
                try:
                    self.player_tree.insert(
                        parent=i,
                        index="end",
                        iid=k.position,
                        text="",
                        values=(k.name, k.value()),
                        tag=k.hex,
                    )
                except:
                    self.player_tree.insert(
                        parent=i,
                        index="end",
                        iid=k.position,
                        text="",
                        values=(k.name, k.value()),
                    )
                count += 1
        for i, j in self.properties.items():
            try:
                self.player_tree.tag_configure(j.hex, background=j.hex)
            except:
                pass

        self.player_tree.place(relx=0, rely=0.5, anchor="w", relheight=1, relwidth=0.95)
        self.player_tree.bind(
            "<<TreeviewSelect>>", lambda event: self.treeview_click(event)
        )

    def treeview_click(self, event):
        try:
            self.property_frame_popup(int(self.player_tree.focus()))
        except:
            pass

    def open_children(self, colour):
        for i in self.player_tree.selection():
            self.player_tree.selection_remove(i)
        for i in self.player_details:
            if self.player_tree.item(i, "open"):
                self.player_tree.item(i, open=False)

        for i, j in self.player_details.items():
            if j["Colour"] == colour:
                self.player_tree.item(i, open=True)
                self.player_tree.selection_set(i)

    # endregion

    def action_frame_popup(self, txt):
        self.action_frame = tk.Frame(
            self.main_frame,
            width=(self.board_side - 2) // 1,
            height=(self.board_side - 2) // 2.45,
        )

        self.action_frame.place(relx=0, rely=0, anchor="nw")

        if self.turn != self.me:
            not_your_turn = tk.Label(
                self.action_frame,
                text=f'{self.player_details[self.turn]["Name"]} is playing!',
                font=50,
            )
            not_your_turn.place(relx=0.5, rely=0.5, anchor="center")
        else:
            self.buy_button = ttk.Button(
                self.action_frame,
                text="BUY",
                style="my.TButton",
                command=lambda: self.buy_property(
                    self.player_details[self.turn]["Position"] % 40, self.turn
                ),
                state="disabled",
            )

            self.buy_button.place(relx=0.2, rely=0.1, anchor="center")

            my_sets = []
            for i in self.player_details[self.turn]["Properties"]:
                if (
                    i.houses >= 0
                    and i.colour not in my_sets
                    and i.colour not in ["Station", "Utility"]
                ):
                    my_sets.append(i.colour)

            self.build_button = ttk.Button(
                self.action_frame,
                text="BUILD",
                style="my.TButton",
                command=self.build_action_frame,
            )
            self.build_button.place(relx=0.2, rely=0.4, anchor="center")

            if not my_sets:
                self.build_button.configure(state="disabled")

            self.mortgage_button = ttk.Button(
                self.action_frame,
                text="MORTGAGE",
                style="my.TButton",
            )  # command=lambda: self.mortgage(),
            self.mortgage_button.place(relx=0.8, rely=0.1, anchor="center")

            if not self.player_details[self.turn]["Properties"]:
                self.mortgage_button.configure(state="disabled")

            self.trade_button = ttk.Button(
                self.action_frame,
                text="TRADE",
                style="my.TButton",
            )  # command=lambda: self.trade(),
            self.trade_button.place(relx=0.8, rely=0.4, anchor="center")

            if not self.player_details[self.turn]["Properties"]:
                self.trade_button.configure(state="disabled")

            self.end_button = ttk.Button(
                self.action_frame,
                text="END TURN",
                style="my.TButton",
                command=lambda: self.end_turn(),
            )
            self.end_button.place(relx=0.5, rely=0.25, anchor="center")
            if str(self.roll_button["state"]) == "normal":
                self.end_button.configure(state="disabled")

            self.current_txt = txt

            action_label = tk.Label(self.action_frame, text=self.current_txt, font=30)
            action_label.place(relx=0.5, rely=0.75, anchor="center")

    def toggle_action_buttons(self, enable=False):
        if enable:
            state = "normal"
        else:
            state = "disabled"
        d = {
            "end": self.end_button,
            "buy": self.buy_button,
            "build": self.build_button,
            "mortgage": self.mortgage_button,
            "trade": self.trade_button,
        }
        for i in d:
            if d[i].winfo_exists():
                d[i].configure(state=state)
                if i == "trade":
                    if not self.player_details[self.turn]["Properties"]:
                        d[i].configure(state="disabled")
                if i == "end":
                    if str(self.roll_button["state"]) == "normal":
                        d[i].configure(state="disabled")
                if i == "mortgage":
                    if not self.player_details[self.turn]["Properties"]:
                        d[i].configure(state="disabled")
                if i == "build":
                    my_sets = []
                    for j in self.player_details[self.turn]["Properties"]:
                        if (
                            j.houses >= 0
                            and j.colour not in my_sets
                            and j.colour not in ["Station", "Utility"]
                        ):
                            my_sets.append(i.colour)
                    if not my_sets:
                        d[i].configure(state="disabled")
                if i == "buy":
                    if not bool(
                        self.properties[
                            self.player_details[self.turn]["Position"] % 40
                        ].colour
                    ) or (
                        self.properties[
                            self.player_details[self.turn]["Position"] % 40
                        ].owner
                    ):
                        d[i].configure(state="disabled")

    def buy_property(self, propertypos, buyer, received=False):
        self.toggle_action_buttons()
        if not received:
            if self.show_message(
                f"Buy {self.properties[propertypos].name}?",
                f"You'll be buying {self.properties[propertypos].name} for {self.properties[propertypos].price}, leaving {(self.player_details[buyer]['Money'])-self.properties[propertypos].price} cash with you",
                type="okcancel",
            ):
                pass
            else:
                self.update_game("Buy")
                self.toggle_action_buttons(True)
                return
        if self.properties[propertypos].colour:
            if not self.properties[propertypos].owner:
                self.properties[propertypos].owner = buyer
                l = self.player_details[buyer]["Properties"]
                l.append(self.properties[propertypos])
                self.player_details[buyer]["Money"] -= self.properties[
                    propertypos
                ].price
                # Inserting Properties in Sorted order
                l.sort(key=lambda i: i.position)
                for i in range(len(l)):
                    if l[i].colour == "Station":
                        l.append(l.pop(i))
                for i in range(len(l)):
                    if l[i].colour == "Utility":
                        l.append(l.pop(i))

                self.player_details[buyer].update({"Properties": l})
                if self.properties[propertypos].colour in [
                    "Brown",
                    "Dark Blue",
                ]:
                    colour_set = 2
                else:
                    colour_set = 3

                if self.count_colour(propertypos) == colour_set:
                    for i in self.properties.values():
                        if i.colour == self.properties[propertypos].colour:
                            i.houses = 0
            else:
                print("Owned")
        else:
            print("Can't Buy")
        self.update_game("Default")
        if not received:
            self.send_msg(("BUY", propertypos))

    def build_action_frame(self):
        self.build_frame = tk.Frame(
            self.action_frame,
            width=(self.board_side - 2) // 1,
            height=(self.board_side - 2) // 2.45,
        )
        self.build_frame.place(relx=0, rely=0, anchor="nw")

        tk.Button(
            self.build_frame,
            text="← BACK",
            font=("times", (self.board_side - 2) // 60),
            highlightthickness=0,
            border=0,
            command=self.build_frame.destroy,
        ).place(relx=0.1, rely=0.05, anchor="ne")

        self.bind("<Escape>", lambda a: self.build_frame.destroy())

        my_sets = []
        for i in self.player_details[self.turn]["Properties"]:
            if (
                i.houses >= 0
                and i.colour not in my_sets
                and i.colour not in ["Station", "Utility"]
            ):
                my_sets.append(i.colour)

        tk.Label(
            self.build_frame,
            text="Select the Colour Set: ",
            font=("times", (self.board_side - 2) // 50),
        ).place(relx=0.1, rely=0.2, anchor="nw")
        self.select_set = ttk.Combobox(self.build_frame, value=my_sets, width=15)
        self.select_set.place(relx=0.5, rely=0.2, anchor="nw")

        def distribute_build(event, set_properties):
            try:
                for i, j in self.radio_dict.items():
                    j.destroy()
            except:
                pass
            if self.extrahouse_label.winfo_exists():
                self.extrahouse_label.destroy()

            total_houses = int(self.select_houses.get())
            no_of_properties = len(set_properties.values())
            old_houses = list(set_properties.values())
            plot = [(i, old_houses[i]) for i in range(len(old_houses))]
            if no_of_properties == 3 and sum(old_houses) % 3 == 1 and total_houses == 1:
                plot = sorted(plot, key=lambda x: x[-1])
                self.new_building = [0, 0, 0, 1, (plot[0][0], plot[1][0])]
            else:
                base = (sum(old_houses) + total_houses) // no_of_properties
                self.new_building = (
                    [base - i for i in old_houses]
                    + [(sum(old_houses) + total_houses) % no_of_properties]
                    + [tuple(range(0, len(old_houses)))]
                )
            new_before_extra = copy.deepcopy(self.new_building)

            def final_text_func():
                d = {
                    0: "0 Houses",
                    1: "1 House",
                    2: "2 Houses",
                    3: "3 Houses",
                    4: "4 Houses",
                    5: "A Hotel",
                }
                finaltxt = f"You will have"
                for i in range(len(self.new_building[:-2])):
                    finaltxt += f"\n→{d[old_houses[i]+self.new_building[i]]} on {list(set_properties.keys())[i].name}"
                finaltxt += f"\n on paying {list(set_properties.keys())[0].build * total_houses}"
                if self.final_build_txt_label.winfo_exists():
                    self.final_build_txt_label.destroy()
                self.final_build_txt_label = tk.Label(
                    self.build_frame,
                    text=finaltxt,
                    font=("times", (self.board_side - 2) // 50),
                )
                self.final_build_txt_label.place(relx=0.5, rely=0.5, anchor="nw")

            def extrahouse_clicked(val, opposite):
                if sum(self.new_building[:-2]) >= total_houses:
                    self.new_building = copy.deepcopy(new_before_extra)
                if opposite:
                    for i in range(len(self.new_building[:-2])):
                        if i != val:
                            self.new_building[i] += 1
                else:
                    self.new_building[val] += 1

                final_text_func()

            if self.new_building[-2]:
                extrahouse = tk.IntVar()
                extrahouse_txt = "Build Extra House on?"
                if self.new_building[-2] == 1:
                    extrahouse.set(len(self.new_building) - 3)
                    opp = False

                elif self.new_building[-2] == 2:
                    extrahouse_txt = "DONT " + extrahouse_txt
                    opp = True
                self.extrahouse_label = tk.Label(
                    self.build_frame,
                    text=extrahouse_txt,
                    font=("times", (self.board_side - 2) // 50),
                )
                self.extrahouse_label.place(relx=0.1, rely=0.5, anchor="nw")

                extrahouse_clicked(extrahouse.get(), opp)
                k = 0
                for i in set_properties:
                    if k in self.new_building[-1]:
                        self.radio_dict[i.name + " Button"] = ttk.Radiobutton(
                            self.build_frame,
                            text=i.name,
                            variable=extrahouse,
                            value=k,
                            command=lambda: extrahouse_clicked(extrahouse.get(), opp),
                        )
                        self.radio_dict[i.name + " Button"].place(
                            relx=0.1, rely=0.6 + (k / 10), anchor="nw"
                        )
                    k += 1
            else:
                final_text_func()

            def build_all():
                conftxt = f"Are you sure you want to pay {list(set_properties.keys())[0].build * total_houses} to build on the {list(set_properties.keys())[0].colour} set, leaving {(self.player_details[self.me]['Money'])-list(set_properties.keys())[0].build * total_houses} cash with you"

                if self.show_message(
                    f"Confirm Build",
                    conftxt,
                    type="okcancel",
                ):
                    for i in range(len(self.new_building[:-2])):
                        self.build(
                            list(set_properties.keys())[i].position,
                            self.new_building[i],
                        )

            self.final_build_button = tk.Button(
                self.build_frame,
                text="BUILD",
                font=("times", (self.board_side - 2) // 60),
                command=build_all,
            )
            self.final_build_button.place(relx=0.75, rely=0.9, anchor="nw")

            self.clear_build_button = tk.Button(
                self.build_frame,
                text="CLEAR",
                font=("times", (self.board_side - 2) // 60),
                command=lambda: clear_all(True),
            )
            self.clear_build_button.place(relx=0.9, rely=0.9, anchor="nw")

        def clear_all(all):
            try:
                for i, j in self.radio_dict.items():
                    j.destroy()
            except:
                pass
            try:
                self.extrahouse_label.destroy()
                self.final_build_txt_label.destroy()
                self.clear_build_button.destroy()
                self.final_build_button.destroy()
            except:
                pass
            if all:
                self.select_set.set("")
                try:
                    self.select_houses.destroy()
                    self.select_houses_label.destroy()
                except:
                    pass

        def selected(event):
            clear_all(False)
            selected_set = self.select_set.get()
            set_properties = {}
            for i in self.player_details[self.turn]["Properties"]:
                if i.colour == selected_set:
                    set_properties[i] = i.houses
            houses_possible = 0
            if len(set_properties) == 2:
                houses_possible = 10 - sum(set_properties.values())
            else:
                houses_possible = 15 - sum(set_properties.values())

            if (
                list(set_properties.keys())[0].build * houses_possible
                > self.player_details[self.me]["Money"]
            ):
                houses_possible = (
                    self.player_details[self.me]["Money"]
                    // list(set_properties.keys())[0].build
                )

            self.houses_list = list(range(1, houses_possible + 1))
            self.select_houses_label = tk.Label(
                self.build_frame,
                text="Select the Number of Houses: ",
                font=("times", (self.board_side - 2) // 50),
            )
            self.select_houses_label.place(relx=0.1, rely=0.35, anchor="nw")
            self.select_houses = ttk.Combobox(
                self.build_frame, value=self.houses_list, width=15
            )
            self.select_houses.place(relx=0.5, rely=0.35, anchor="nw")

            self.radio_dict = {}
            self.extrahouse_label = None
            self.select_houses.bind(
                "<<ComboboxSelected>>",
                lambda event: distribute_build(event, set_properties),
            )
            self.select_houses.bind(
                "<KeyRelease>", lambda event: search(event, "houses")
            )

        self.select_set.bind("<<ComboboxSelected>>", selected)
        self.select_set.bind("<KeyRelease>", lambda event: search(event, "set"))

        def search(event, combobox):
            value = event.widget.get()
            if combobox == "set":
                if value:
                    data = []
                    for i in my_sets:
                        if value.lower() in i.lower():
                            data.append(i)

                    self.select_set.configure(values=data)
                else:
                    self.select_set.configure(values=my_sets)
            elif combobox == "houses":
                if value:
                    data = []
                    for i in self.houses_list:
                        if value.lower() in str(i):
                            data.append(i)

                    self.select_houses.configure(values=data)
                else:
                    self.select_houses.configure(values=self.houses_list)

    def build(self, property, number, received=False):
        if self.properties[property].owner:
            if self.properties[property].houses + number > 5:
                print("ERROR! Can't build more than 5")
            else:
                self.properties[property].houses += number
                self.player_details[self.properties[property].owner]["Money"] -= (
                    self.properties[property].build * number
                )
            self.place_houses()
            self.update_game()
        else:
            print("Bruh Die")

        if not received:
            self.send_msg(("BUILD", property, number))

    def roll_dice(self, roll=None, received=False, cli=False):
        try:
            music(ASSET + "/Die/diceroll.mp3")
        except:
            pass
        dice_roll = roll if received else (random.randint(1, 6), random.randint(1, 6))
        dice_roll = roll if cli else dice_roll
        if not received:
            self.send_msg(("ROLL", dice_roll))
        for i in range(18):
            self.dice_spot1.configure(image=self.die_dict[random.randint(1, 6)])
            self.dice_spot2.configure(image=self.die_dict[random.randint(1, 6)])
            self.dice_spot1.update()
            self.dice_spot2.update()
            sleep(0.12)
            self.roll_button.configure(state="disabled")
        self.dice_spot1.configure(image=self.die_dict[dice_roll[0]])
        self.dice_spot2.configure(image=self.die_dict[dice_roll[1]])
        self.dice_spot1.update()
        self.dice_spot2.update()
        self.current_move = sum(dice_roll)
        if dice_roll[0] == dice_roll[1]:
            self.move(self.turn, self.current_move, endturn=False)
            self.doubles_counter += 1
        else:
            self.doubles_counter = 0
            self.move(self.turn, self.current_move, endturn=True)
        if self.doubles_counter == 3:
            self.move(self.turn, self.current_move, endturn=True)
            # TODO GO TO JAIL #END TURN AUTOMATICALLY
            self.action_frame_popup("Jail")

    def show_message(self, title, message, type="info", timeout=0):
        mbwin = tk.Tk()
        mbwin.withdraw()
        try:
            if timeout:
                mbwin.after(timeout, mbwin.destroy)
            if type == "info":
                msgb.showinfo(title, message, master=mbwin)
            elif type == "warning":
                msgb.showwarning(title, message, master=mbwin)
            elif type == "error":
                msgb.showerror(title, message, master=mbwin)
            elif type == "okcancel":
                okcancel = msgb.askokcancel(title, message, master=mbwin)
                return okcancel
            elif type == "yesno":
                yesno = msgb.askyesno(title, message, master=mbwin)
                return yesno
        except:
            print("Error")

    def click_to_position(self, event):
        x, y = event.x, event.y
        l = [1.6, 1.6]
        l[1:1] = [1] * 9
        pos = None
        if x <= self.property_height:
            for i in range(len(l)):
                if y > sum(l[i + 1 :]) / sum(l) * self.board_side:
                    pos = 10 + i
                    break
        elif x >= self.board_side - self.property_height:
            for i in range(len(l)):
                if y > sum(l[i + 1 :]) / sum(l) * self.board_side:
                    pos = (40 - i) % 40
                    break
        elif y <= self.property_height:
            for i in range(len(l)):
                if x > sum(l[i + 1 :]) / sum(l) * self.board_side:
                    pos = 30 - i
                    break
        elif y >= self.board_side - self.property_height:
            for i in range(len(l)):
                if x > sum(l[i + 1 :]) / sum(l) * self.board_side:
                    pos = i
                    break
        if pos in [10, 30]:
            self.show_message("Jail Rules", "Jail Rules", timeout=2000)
        elif pos == 20:
            self.show_message("Free Parking", "Do Nothing!", timeout=2000)
        elif pos == 0:
            self.show_message("GO!", "Collect 200 Salary as you pass GO!", timeout=2000)
        elif pos in [2, 17, 33]:
            self.show_message("Community Chest", "Do as directed on card", timeout=2000)
        elif pos in [7, 22, 36]:
            self.show_message("Chance", "Do as directed on card", timeout=2000)
        elif pos == 4:
            self.show_message(
                "Income Tax", "Pay 200 as Tax on landing here", timeout=2000
            )
        elif pos == 38:
            self.show_message(
                "Super Tax", "Pay 100 as Tax on landing here", timeout=2000
            )
        elif pos:
            self.property_frame_popup(pos)

    def position_to_xy(
        self, position
    ):  # +1, +2, because canvas has random error and places image 2,2 up and left, so image is placed at 2,2 and not 0,0
        l = [1.6, 1.6]
        l[1:1] = [1] * 9
        position %= 40
        if position == 0:
            x1 = self.board_side + 1
            y1 = self.board_side - self.property_height + 2
        elif position <= 10:
            x1 = sum(l[:-(position)]) * self.property_width + 1
            y1 = self.board_side - self.property_height + 2
        elif position <= 20:
            x1 = self.property_height + 2
            y1 = sum(l[: -(position - 9)]) * self.property_width + 1
        elif position <= 30:
            x1 = sum(l[: (position - 19)]) * self.property_width + 1
            y1 = 0 + 2
        elif position < 40:
            x1 = self.board_side + 2
            y1 = sum(l[: (position - 30)]) * self.property_width + 1
        # self.board_canvas.create_rectangle(x1,y1,x1-self.property_height,y1+self.property_height,outline='blue',width=3)
        return x1, y1

    def position_to_tokenxy(self, player, position):
        position %= 40

        x1, y1 = self.position_to_xy(position)
        if position == 10:
            if self.player_details[player]["Injail"]:
                x = x1 - (self.property_height * 0.35)
                y = y1 + (self.property_height * 0.35)
            else:
                if self.player_details[player]["Colour"] == "red":
                    return int(
                        self.token_width / 2 + self.property_height * 0.075
                    ), int(y1 + self.property_height * 0.3 - self.token_width / 2)
                elif self.player_details[player]["Colour"] == "green":
                    return int(
                        self.token_width / 2 + self.property_height * 0.075
                    ), int(y1 + self.property_height * 0.6 - self.token_width / 2)
                elif self.player_details[player]["Colour"] == "blue":
                    return int(
                        x1 - self.property_height * 0.6 + self.token_width / 2 + 3
                    ), int(y1 + self.property_height * 0.95 - self.token_width / 2)
                elif self.player_details[player]["Colour"] == "gold":
                    return int(
                        x1 - self.property_height * 0.3 + self.token_width / 2 + 3
                    ), int(y1 + self.property_height * 0.95 - self.token_width / 2)
                else:
                    print("You died")
        elif not position % 10:
            x = x1 - (self.property_height * 0.5)
            y = y1 + (self.property_height * 0.5)
        elif position < 10:
            x = x1 - (self.property_width * 0.5)
            y = y1 + (self.property_height * 0.6)
        elif position < 20:
            x = x1 - (self.property_height * 0.6)
            y = y1 + (self.property_width * 0.5)
        elif position < 30:
            x = x1 - (self.property_width * 0.5)
            y = y1 + (self.property_height * 0.4)
        elif position < 40:
            x = x1 - (self.property_height * 0.4)
            y = y1 + (self.property_width * 0.5)

        if self.player_details[player]["Colour"] == "red":
            return int(x - self.token_width / 2 - 1), int(y - self.token_width / 2)
        elif self.player_details[player]["Colour"] == "green":
            return int(x + self.token_width / 2 + 1), int(y - self.token_width / 2)
        elif self.player_details[player]["Colour"] == "blue":
            return int(x - self.token_width / 2 - 1), int(y + self.token_width / 2 + 2)
        elif self.player_details[player]["Colour"] == "gold":
            return int(x + self.token_width / 2 + 1), int(y + self.token_width / 2 + 2)

    def place_houses(self):
        HOUSES = ASSET + "/Houses"
        d = {
            1: ["house_1", 0.2],
            2: ["house_2", 0.36],
            3: ["house_3", 0.54],
            4: ["house_4", 0.6],
            5: ["hotel", 0.2],
        }
        for i, j in self.properties.items():
            if j.hex:
                if j.houses > 0:
                    x1, y1 = self.position_to_xy(i)
                    size = [d[j.houses][1], 0.2]
                    if i < 10:
                        x = x1 - self.property_width / 2
                        y = y1 + self.property_height * 0.1
                        rotation = "down"
                    elif i < 20:
                        x = x1 - self.property_height * 0.1
                        y = y1 + self.property_width / 2
                        rotation = "left"
                        size = size[::-1]
                    elif i < 30:
                        x = x1 - self.property_width / 2
                        y = y1 + self.property_height * 0.9
                        rotation = "up"
                    else:
                        x = x1 - self.property_height * 0.9
                        y = y1 + self.property_width / 2
                        rotation = "right"
                        size = size[::-1]
                    house_image = ImageTk.PhotoImage(
                        ImageOps.expand(
                            Image.open(HOUSES + f"/{d[j.houses][0]}_{rotation}.png")
                        ).resize(
                            (
                                int((self.property_height) * size[0]),
                                int((self.property_height) * size[1]),
                            ),
                            Image.Resampling.LANCZOS,
                        )
                    )

                    self.house_images.append(house_image)
                    self.board_canvas.create_image(x, y, image=self.house_images[-1])

    def pass_go(self, player):
        self.player_details[player]["Money"] += 200
        self.update_game("You received 200 as salary!")

    def move(self, player, move, endturn=False, showmove=True):
        colour = self.player_details[player]["Colour"]
        self.colour_token_dict = {
            "red": self.red_token,
            "green": self.green_token,
            "blue": self.blue_token,
            "gold": self.yellow_token,
        }

        if move and showmove:
            for i in range(move):
                self.player_details[player]["Position"] += 1
                x1, y1 = self.position_to_tokenxy(
                    player, self.player_details[player]["Position"]
                )
                self.colour_token_dict[colour].place(x=x1, y=y1, anchor="center")
                sleep(0.2)
                self.colour_token_dict[colour].update()
                if not self.player_details[player]["Position"] % 40:
                    self.pass_go(player)
        else:
            self.player_details[player]["Position"] += move
            x1, y1 = self.position_to_tokenxy(
                player, self.player_details[player]["Position"]
            )
            self.colour_token_dict[colour].place(x=x1, y=y1, anchor="center")

        pos = self.player_details[player]["Position"] % 40

        if endturn:
            self.roll_button.configure(state="disabled")
            if self.end_button.winfo_exists():
                self.end_button.configure(state="normal")
        else:
            self.roll_button.configure(state="normal")
            if self.end_button.winfo_exists():
                self.end_button.configure(state="disabled")

        if pos in [10, 30]:
            self.update_game("Jail")
        elif pos in [0, 4, 20, 38]:
            self.update_game("Default")
        elif pos in [2, 17, 33]:
            self.update_game("Community Chest")
        elif pos in [7, 22, 36]:
            self.update_game("Chance")
        elif pos:
            self.property_frame_popup(pos)
            if self.properties[pos].owner:
                self.pay_rent(self.turn, pos)
            else:
                self.update_game("Buy")
                if self.turn == self.me:
                    self.buy_button.configure(state="normal")

    def pay_rent(self, payer, propertypos):
        rent_amt = self.properties[propertypos].rent()
        while self.player_details[payer]["Money"] < rent_amt:
            # self.end_button.configure(state='disabled')
            # Mortgage pop up
            # Disable everything except mortgage
            self.update_game(
                f"You don't have enough money to pay!\nMortgage properties or sell houses worth {rent_amt- self.player_details[payer]['Money']}"
            )
        self.player_details[payer]["Money"] -= rent_amt
        self.player_details[self.properties[propertypos].owner]["Money"] += rent_amt
        self.update_game(
            f"{self.player_details[payer]['Name']} paid {rent_amt} to {self.player_details[self.properties[propertypos].owner]['Name']}"
        )

    def end_turn(self, received=False):
        self.toggle_action_buttons()
        if not received:
            if self.show_message(
                "End Turn?",
                f"{self.player_details[self.turn]['Name']}, are you sure you want to end your turn?",
                type="yesno",
            ):
                pass
            else:
                self.update_game()
                self.toggle_action_buttons(True)
                return
        try:
            self.turn = self.uuids[self.uuids.index(self.turn) + 1]
        except:
            self.turn = self.uuids[0]

        if self.turn == self.me:
            self.roll_button.configure(state="normal")

        if not received:
            self.send_msg(("END",))

        self.update_game("It's your turn now! Click 'Roll Dice'")

    def CLI(self):
        while True:
            t = tuple(i for i in input().split())
            if t:
                if t[0] == "roll":
                    try:
                        self.roll_dice(roll=(int(t[1]), int(t[2])), cli=True)
                    except:
                        pass
                elif t[0] == "buy":
                    for i in t[1:]:
                        self.buy_property(int(i), self.me)

                elif t[0] == "build":
                    try:
                        self.build(int(t[1]), int(t[2]))
                    except:
                        pass
                else:
                    print("Die")
            else:
                print("Closed CLI Thread")
                break


# TODO Rent for station, utility
# TODO: Mortgage, Bankruptcy, Jail, Tax, Trading, Chance, Community Chest, All Rules & Texts, Update GUI

# ? Voice Chat, Auctions, Select Colour, Custom Actions

# ! Fix running monopoly separately
if __name__ == "__main__":
    mono = None
    root = tk.Tk()
    tk.Button(root, text="START", command=lambda: cobj.send(("START",))).pack()

    def updater(msg):
        global mono
        if msg[0] == "START":
            mono = Monopoly(msg[1], msg[2], cobj, hobj)
            cobj.updater = mono.updater
            root.withdraw()

    cobj = Client(("localhost", 6788), updater)
    hobj = Http("http://167.71.231.52:5000")
    hobj.login(input("Username: "), input("Password: "))

    root.mainloop()