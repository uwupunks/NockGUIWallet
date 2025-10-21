"""UI styles configuration for the Nockchain GUI Wallet."""

import tkinter as tk
from tkinter import ttk

from constants import COLORS, FONT_FAMILY


def setup_styles(root: tk.Tk) -> None:
    style = ttk.Style(root)
    style.theme_create(
        "modern",
        parent="clam",
        settings={
            "TButton": {
                "configure": {
                    "padding": [20, 10, 20, 10],
                    "font": (FONT_FAMILY, 10, "bold"),
                }
            },
            "Primary.TButton": {
                "configure": {
                    "background": COLORS["primary"],
                    "foreground": "white",
                },
                "map": {
                    "background": [
                        ("active", COLORS["primary_hover"]),
                        ("disabled", "#9CA3AF"),
                    ]
                },
            },
            "Secondary.TButton": {
                "configure": {
                    "background": COLORS["secondary"],
                    "foreground": "white",
                },
                "map": {
                    "background": [
                        ("active", COLORS["secondary_hover"]),
                        ("disabled", "#9CA3AF"),
                    ]
                },
            },
            "Success.TButton": {
                "configure": {
                    "background": COLORS["success"],
                    "foreground": "white",
                },
                "map": {
                    "background": [
                        ("active", COLORS["success_hover"]),
                        ("disabled", "#9CA3AF"),
                    ]
                },
            },
            "Danger.TButton": {
                "configure": {
                    "background": COLORS["danger"],
                    "foreground": "white",
                },
                "map": {
                    "background": [
                        ("active", COLORS["danger_hover"]),
                        ("disabled", "#9CA3AF"),
                    ]
                },
            },
            "TFrame": {
                "configure": {
                    "background": COLORS["input_background"],
                }
            },
            "TLabel": {
                "configure": {
                    "background": COLORS["input_background"],
                    "foreground": COLORS["text"],
                    "font": (FONT_FAMILY, 10),
                }
            },
            "Modern.TFrame": {"configure": {"background": COLORS["input_background"]}},
            "ModernTitle.TFrame": {
                "configure": {"background": COLORS["input_background"]}
            },
            "ModernTitle.TLabel": {
                "configure": {
                    "background": COLORS["input_background"],
                    "foreground": COLORS["text"],
                    "font": (FONT_FAMILY, 12, "bold"),
                    "padding": 10,
                }
            },
            "ModernBorder.TFrame": {"configure": {"background": COLORS["border"]}},
            "Status.TFrame": {"configure": {"background": COLORS["background"]}},
            "Input.TFrame": {"configure": {"background": COLORS["input_background"]}},
            "White.TFrame": {"configure": {"background": COLORS["input_background"]}},
            "Addr.TFrame": {"configure": {"background": COLORS["input_background"]}},
            "BalanceDetails.TLabel": {
                "configure": {
                    "background": COLORS["input_background"],
                    "foreground": COLORS["text"],
                    "font": (FONT_FAMILY, 14, "bold"),
                }
            },
            "BalanceMain.TLabel": {
                "configure": {
                    "background": COLORS["input_background"],
                    "foreground": COLORS["text"],
                    "font": (FONT_FAMILY, 18, "bold"),
                }
            },
            "SectionTitle.TLabel": {
                "configure": {
                    "background": COLORS["input_background"],
                    "foreground": COLORS["text"],
                    "font": (FONT_FAMILY, 12, "bold"),
                }
            },
            "Key.TLabel": {
                "configure": {
                    "background": COLORS["input_background"],
                    "foreground": COLORS["text_light"],
                    "font": ("Consolas", 9),
                }
            },
            "Price.TLabel": {
                "configure": {
                    "background": COLORS["background"],
                    "font": (FONT_FAMILY, 10, "bold"),
                    "foreground": "white",
                }
            },
            "Change.TLabel": {
                "configure": {
                    "background": COLORS["background"],
                    "font": (FONT_FAMILY, 10, "bold"),
                }
            },
            "Node.TLabel": {
                "configure": {
                    "background": COLORS["background"],
                    "font": (FONT_FAMILY, 10),
                }
            },
            "Connection.TLabel": {
                "configure": {
                    "background": COLORS["background"],
                    "foreground": "white",
                    "font": (FONT_FAMILY, 10),
                }
            },
            "Time.TLabel": {
                "configure": {
                    "background": COLORS["background"],
                    "foreground": "white",
                    "font": (FONT_FAMILY, 10),
                }
            },
        },
    )
    style.theme_use("modern")
