# KAFAYI YEMIŞ BIR ADAM TARAFINDAN YAPILDI HABERIN OLSUN !
# ha bidee telif hakkı var kopyalarsan sen gg olursun karşı taraf değil .d

import sounddevice as sd
import numpy as np
import tkinter as tk
from tkinter import ttk
import keyboard

class AudioProcessor:
    def __init__(self):
        self.active = False
        self.input_device = None
        self.output_device = None
        self.stream = None
        self.gain = 1.0
        self.distortion = 1.0
        self.clipping = 1.0
        self.effects_enabled = False

    def get_device_list(self, device_type):
        devices = []
        device_list = sd.query_devices()

        for i, dev in enumerate(device_list):
            try:
                # Sadece MME host API'sini kullan (Windows için)
                host_api_info = sd.query_hostapis(dev['hostapi'])
                if host_api_info['name'] != 'MME':
                    continue

                if device_type == 'input' and dev['max_input_channels'] > 0:
                    devices.append(f"{i}: {dev['name']}")
                elif device_type == 'output' and dev['max_output_channels'] > 0:
                    devices.append(f"{i}: {dev['name']}")
            except Exception as e:
                print(f"Device {i} error: {e}")
                continue

        return devices

    def process_audio(self, indata, outdata, frames, time, status):
        try:
            if status:
                print(f"Status: {status}")

            audio_data = indata[:, 0].copy()  # Mono kanal al

            if self.effects_enabled:
                # ✅ SES EFEKTLERİ GERİ EKLENDİ
                # Apply gain
                audio_data = audio_data * (self.gain ** 2)

                # Apply distortion
                audio_data = np.tanh(audio_data * self.distortion * 10)

                # Stack another layer of distortion for more intensity
                audio_data = np.tanh(audio_data * 2)

                # Apply clipping
                audio_data = np.clip(audio_data, -self.clipping, self.clipping)

            # Çıkışa yaz
            outdata[:, 0] = audio_data

        except Exception as e:
            print(f"Audio processing error: {e}")
            outdata[:] = indata

    def start_stream(self, input_device_index, output_device_index):
        if self.stream is not None:
            self.stop_stream()

        try:
            self.stream = sd.Stream(
                device=(input_device_index, output_device_index),
                samplerate=44100,
                channels=1,
                dtype=np.float32,
                callback=self.process_audio,
                blocksize=1024
            )
            self.stream.start()
        except Exception as e:
            raise Exception(f"Stream başlatılamadı: {str(e)}")

    def stop_stream(self):
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception as e:
                print(f"Stream kapatma hatası: {e}")
            finally:
                self.stream = None

    def cleanup(self):
        self.stop_stream()


class AudioEffectGUI:
    def __init__(self):
        self.processor = AudioProcessor()
        self.root = tk.Tk()
        self.root.title("PASHA KULAKLIK GG")
        self.root.geometry("500x600")

        style = ttk.Style()
        style.theme_use('clam')

        self.toggle_key = "f6"
        self.is_stream_active = False

        self.profile_settings = {
            "Ses arttırma": {"gain": 1.0, "distortion": 1.0, "clipping": 1.0},
            "Kızarmış ses": {"gain": 5.0, "distortion": 20.0, "clipping": 0.5},
            "Cinnet modu": {"gain": 10.0, "distortion": 35.0, "clipping": 0.3}
        }

        self.setup_ui()
        self.setup_hotkey()

        # Pencere kapatılırken cleanup
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(padx=10, pady=10, fill="both", expand=True)

        input_frame = ttk.LabelFrame(main_frame, text="Ses Aygıtları")
        input_frame.pack(padx=5, pady=5, fill="x")

        ttk.Label(input_frame, text="Mikrofonunuzu seçin:").pack(pady=2)
        self.input_device_var = tk.StringVar()
        self.input_device_combo = ttk.Combobox(input_frame, textvariable=self.input_device_var, state="readonly")
        self.input_device_combo['values'] = self.processor.get_device_list('input')
        if self.input_device_combo['values']:
            self.input_device_combo.current(0)
        self.input_device_combo.pack(padx=5, pady=5, fill="x")

        ttk.Label(input_frame, text="Çıkış (CABLE INPUT-VB-Cable):").pack(pady=2)
        self.output_device_var = tk.StringVar()
        self.output_device_combo = ttk.Combobox(input_frame, textvariable=self.output_device_var, state="readonly")
        self.output_device_combo['values'] = self.processor.get_device_list('output')
        if self.output_device_combo['values']:
            self.output_device_combo.current(0)
        self.output_device_combo.pack(padx=5, pady=5, fill="x")

        # Refresh button ekle
        refresh_btn = ttk.Button(input_frame, text="🔄 Cihazları Yenile", command=self.refresh_devices)
        refresh_btn.pack(padx=5, pady=5)

        profile_frame = ttk.LabelFrame(main_frame, text="Profil Seçimi")
        profile_frame.pack(padx=5, pady=5, fill="x")

        ttk.Label(profile_frame, text="Ön ayarlar:").pack(pady=2)
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(profile_frame, textvariable=self.profile_var, state="readonly")
        self.profile_combo['values'] = list(self.profile_settings.keys())
        self.profile_combo.current(0)
        self.profile_combo.pack(padx=5, pady=5, fill="x")
        self.profile_combo.bind("<<ComboboxSelected>>", self.apply_profile)

        controls_frame = ttk.LabelFrame(main_frame, text="Ayarlar")
        controls_frame.pack(padx=5, pady=5, fill="x")

        ttk.Label(controls_frame, text="Ses seviyesi:").pack(pady=2)
        self.gain_scale = ttk.Scale(controls_frame, from_=0, to=20, orient="horizontal", command=self.update_gain)
        self.gain_scale.set(self.profile_settings[self.profile_var.get()]["gain"])
        self.gain_scale.pack(fill="x", padx=5, pady=5)

        ttk.Label(controls_frame, text="Bozukluk seviyesi:").pack(pady=2)
        self.distortion_scale = ttk.Scale(controls_frame, from_=1, to=50, orient="horizontal", command=self.update_distortion)
        self.distortion_scale.set(self.profile_settings[self.profile_var.get()]["distortion"])
        self.distortion_scale.pack(fill="x", padx=5, pady=5)

        ttk.Label(controls_frame, text="Kırılma seviyesi:").pack(pady=2)
        self.clipping_scale = ttk.Scale(controls_frame, from_=0.01, to=1, orient="horizontal", command=self.update_clipping)
        self.clipping_scale.set(self.profile_settings[self.profile_var.get()]["clipping"])
        self.clipping_scale.pack(fill="x", padx=5, pady=5)

        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(padx=5, pady=5, fill="x")

        self.toggle_button = ttk.Button(
            buttons_frame,
            text=f"KULAKLARI YOK ET! ({self.toggle_key.upper()})",
            command=lambda: self.toggle_processing(None)
        )
        self.toggle_button.pack(pady=5, fill="x")

        self.extra_info_button = ttk.Button(buttons_frame, text="Program çalışmıyor?", command=self.show_extra_info)
        self.extra_info_button.pack(pady=5, fill="x")

        # Discord link butonu
        discord_btn = ttk.Button(buttons_frame, text="📱 Discord: discord.gg/baRF75wsm2",
                                 command=lambda: self.open_discord())
        discord_btn.pack(pady=5, fill="x")

        self.status_label = ttk.Label(main_frame, text="Durum: RAGE MODE OFF", anchor="center",
                                      font=("Arial", 12, "bold"))
        self.status_label.pack(pady=10, fill="x")

    def refresh_devices(self):
        """Cihaz listesini yenile"""
        self.input_device_combo['values'] = self.processor.get_device_list('input')
        self.output_device_combo['values'] = self.processor.get_device_list('output')

        if self.input_device_combo['values']:
            self.input_device_combo.current(0)
        if self.output_device_combo['values']:
            self.output_device_combo.current(0)

    def apply_profile(self, event=None):
        profile = self.profile_var.get()
        settings = self.profile_settings.get(profile, {})

        self.gain_scale.set(settings.get("gain", 1.0))
        self.distortion_scale.set(settings.get("distortion", 1.0))
        self.clipping_scale.set(settings.get("clipping", 1.0))

        self.processor.gain = float(settings.get("gain", 1.0))
        self.processor.distortion = float(settings.get("distortion", 1.0))
        self.processor.clipping = float(settings.get("clipping", 1.0))

    def setup_hotkey(self):
        keyboard.on_press_key(self.toggle_key, self.toggle_processing)

    def toggle_processing(self, e):
        if not self.input_device_var.get() or not self.output_device_var.get():
            self.status_label.config(text="❌ Hata: Lütfen giriş ve çıkış cihazlarını seçin!")
            return

        # Stream kapatma
        if self.is_stream_active:
            try:
                self.processor.stop_stream()
                self.is_stream_active = False
                self.processor.effects_enabled = False

                self.status_label.config(text="⏹️ Durum: RAGE MODE OFF", foreground="red")
                self.toggle_button.config(text=f"KULAKLARI YOK ET! ({self.toggle_key.upper()})")
                print("🔴 Stream kapatıldı")

            except Exception as err:
                self.status_label.config(text=f"❌ Kapatma hatası: {str(err)}", foreground="red")

        # Stream açma
        else:
            try:
                input_idx = int(self.input_device_var.get().split(':')[0])
                output_idx = int(self.output_device_var.get().split(':')[0])

                self.processor.start_stream(input_idx, output_idx)
                self.processor.effects_enabled = True
                self.is_stream_active = True

                self.status_label.config(text="🔥 Durum: RAGE MODE ON", foreground="green")
                self.toggle_button.config(text=f"NORMAL MODA GEÇ ({self.toggle_key.upper()})")
                print("🟢 Stream başlatıldı")

            except Exception as err:
                self.status_label.config(text=f"❌ Hata: {str(err)}", foreground="red")
                self.is_stream_active = False

    def update_gain(self, value):
        self.processor.gain = float(value)

    def update_distortion(self, value):
        self.processor.distortion = float(value)

    def update_clipping(self, value):
        self.processor.clipping = float(value)

    def open_discord(self):
        import webbrowser
        webbrowser.open("https://discord.gg/baRF75wsm2")

    def show_extra_info(self):
        extra_win = tk.Toplevel(self.root)
        extra_win.title("Yardım")
        extra_win.geometry("450x400")

        extra_text = """
═══════════════════════════════════════
        🎧 PASHA KULAKLIK GGr 🎧
═══════════════════════════════════════

📋 Program çalışmıyor mu? Allah Allah (...)

🔌 Cable input kurulu ama gözükmüyor:
   → 64-bit cable input kurmuş olman gerekiyor
   → Kurduktan sonra restart at

⚠️ Illegal combination hatası:
   → Mikrofonun ve CABLE INPUT kısımlarının 
     doğru seçilmiş olması gerekiyor

❌ Invalid literal hatası:
   → Aga önce bi mikrofonunu seçeydin ya 
     listeden, bu ne acele?

🦠 Abi bu virüs mü?
   → Evet abi bu virüs, çok korkutucu bööö
   → Python uygulamaları sertifika olmadan
     antivirüsü tetikler
   → Keyboard modülü kullandığı için 
     keylogger gibi gözüküyor

💰 Abi bağış kabul ediyor musun?
   → Bu program için hayır
   → Beni mutlu etmek istiyorsan yorumlarına
     bol bol yorum yap, hepsini okuyorum

═══════════════════════════════════════
📱 Discord: discord.gg/baRF75wsm2
🔧 Pasha Network © 2026
═══════════════════════════════════════
        """

        text_widget = tk.Text(extra_win, wrap=tk.WORD, padx=15, pady=15,
                              font=("Consolas", 9), bg="#2b2b2b", fg="white")
        text_widget.insert(1.0, extra_text)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(fill="both", expand=True)

    def on_closing(self):
        try:
            keyboard.unhook_all()
            self.processor.cleanup()
        except Exception as e:
            print(f"Cleanup hatası: {e}")
        finally:
            self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    # ASCII ART BANNER
    print("""
    ██████╗  █████╗ ███████╗██╗  ██╗ █████╗      ██████╗  ██████╗ 
    ██╔══██╗██╔══██╗██╔════╝██║  ██║██╔══██╗    ██╔════╝ ██╔════╝ 
    ██████╔╝███████║███████╗███████║███████║    ██║  ███╗██║  ███╗
    ██╔═══╝ ██╔══██║╚════██║██╔══██║██╔══██║    ██║   ██║██║   ██║
    ██║     ██║  ██║███████║██║  ██║██║  ██║    ╚██████╔╝╚██████╔╝
    ╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝     ╚═════╝  ╚═════╝ 
    """)

    print("🗝️  Pasha Kulaklik GG Baslatildi 💎\n")
    print("🗝️  Keyifli Kullanimlar ! 💎\n")
    print("=" * 60)

    try:
        app = AudioEffectGUI()
        app.run()
    except Exception as e:
        print(f"❌ BOM ! Program GG: {e}")
        input("Press Enter to exit...")