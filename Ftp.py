import sys
import subprocess

def kutuphaneleri_kontrol_et():
    gerekli_paketler = []
    for paket in gerekli_paketler:
        try:
            __import__(paket)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", paket])

kutuphaneleri_kontrol_et()

import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from ftplib import FTP
import os

class FTPClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MİNİOS FTP DOSYA YÖNETİCİSİ")
        self.root.geometry("680x600")
        self.root.resizable(True, True)  # Pencere boyutlandırılabilir
        
        self.ftp = None
        self.su_anki_dizin = "/"

        # --- Stil Ayarları (Yazıların iç içe girmesini önler) ---
        style = ttk.Style()
        style.theme_use("clam")  # Daha modern bir tema
        style.configure("Treeview", 
                        font=("Segoe UI", 10), 
                        rowheight=28,  # Satır yüksekliği artırıldı (ferahlık sağlandı)
                        fieldbackground="#FFFFFF")
        style.configure("Treeview.Heading", 
                        font=("Segoe UI", 10, "bold"), 
                        background="#E0E0E0")

        # --- Sunucu Bilgileri Çerçevesi ---
        frame_baglanti = tk.LabelFrame(root, text=" Sunucu Bağlantı Bilgileri ", font=("Segoe UI", 9, "bold"), padx=10, pady=10)
        frame_baglanti.pack(fill="x", padx=12, pady=8)

        tk.Label(frame_baglanti, text="IP:").grid(row=0, column=0, sticky="w", pady=2)
        self.entry_ip = tk.Entry(frame_baglanti, width=18, font=("Consolas", 10))
        self.entry_ip.insert(0, "192.168.1.")
        self.entry_ip.grid(row=0, column=1, pady=2, padx=5)

        tk.Label(frame_baglanti, text="Port:").grid(row=0, column=2, sticky="w", pady=2)
        self.entry_port = tk.Entry(frame_baglanti, width=6, font=("Consolas", 10))
        self.entry_port.insert(0, "21")
        self.entry_port.grid(row=0, column=3, pady=2, padx=5)

        tk.Label(frame_baglanti, text="Kullanıcı:").grid(row=1, column=0, sticky="w", pady=2)
        self.entry_user = tk.Entry(frame_baglanti, width=18, font=("Consolas", 10))
        self.entry_user.grid(row=1, column=1, pady=2, padx=5)

        tk.Label(frame_baglanti, text="Şifre:").grid(row=1, column=2, sticky="w", pady=2)
        self.entry_pass = tk.Entry(frame_baglanti, show="*", width=6, font=("Consolas", 10))
        self.entry_pass.grid(row=1, column=3, pady=2, padx=5)

        self.btn_connect = tk.Button(frame_baglanti, text="Bağlan", bg="#4CAF50", fg="white", font=("Segoe UI", 9, "bold"), command=self.baglan)
        self.btn_connect.grid(row=2, column=0, columnspan=4, pady=8, sticky="we")

        # --- Konum Göstergesi ---
        frame_yol = tk.Frame(root, padx=12)
        frame_yol.pack(fill="x", padx=5, pady=2)
        tk.Label(frame_yol, text="Mevcut Dizin: ", font=("Segoe UI", 9, "bold")).pack(side="left")
        self.lbl_path = tk.Label(frame_yol, text="/", fg="#1976D2", font=("Consolas", 10, "bold"))
        self.lbl_path.pack(side="left", fill="x")

        # --- Dosya Listesi Çerçevesi ---
        frame_dosyalar = tk.LabelFrame(root, text=" Sunucu İçeriği ", font=("Segoe UI", 9, "bold"), padx=10, pady=10)
        frame_dosyalar.pack(fill="both", expand=True, padx=12, pady=5)

        # Treeview Tablosu
        self.tree = ttk.Treeview(frame_dosyalar, columns=("tur", "isim"), show="headings", selectmode="browse")
        self.tree.heading("tur", text="   Tür")
        self.tree.heading("isim", text="Dosya / Klasör Adı")
        
        # Sütun Genişlikleri ve Hizalama
        self.tree.column("tur", width=110, minwidth=90, anchor="w")
        self.tree.column("isim", width=480, minwidth=200, anchor="w")
        
        self.tree.pack(side="left", fill="both", expand=True)

        # Satır Renk Tag'leri
        self.tree.tag_configure('tek', background='#FFFFFF')
        self.tree.tag_configure('cift', background='#F8F9FA')

        scrollbar = ttk.Scrollbar(frame_dosyalar, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.config(yscrollcommand=scrollbar.set)

        # Çift tıklama olayı
        self.tree.bind("<Double-1>", self.klasore_gir_veya_calistir)

        # --- İşlem Butonları ---
        frame_butonlar = tk.Frame(root, pady=8)
        frame_butonlar.pack(fill="x", padx=12, pady=5)

        self.btn_upload = tk.Button(frame_butonlar, text="⬆ Dosya Yükle", width=15, bg="#2196F3", fg="white", font=("Segoe UI", 9, "bold"), command=self.dosya_yukle)
        self.btn_upload.pack(side="left", padx=4)

        self.btn_download = tk.Button(frame_butonlar, text="⬇ Seçileni İndir", width=15, bg="#FF9800", fg="white", font=("Segoe UI", 9, "bold"), command=self.dosya_indir)
        self.btn_download.pack(side="left", padx=4)

        self.btn_back = tk.Button(frame_butonlar, text="⬅ Üst Klasör", width=13, bg="#757575", fg="white", font=("Segoe UI", 9, "bold"), command=self.ust_klasore_cik)
        self.btn_back.pack(side="left", padx=4)

        self.btn_refresh = tk.Button(frame_butonlar, text="🔄 Yenile", width=10, font=("Segoe UI", 9), command=self.dosyalari_listele)
        self.btn_refresh.pack(side="right", padx=4)

    def baglan(self):
        ip = self.entry_ip.get().strip()
        port = int(self.entry_port.get().strip())
        user = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()

        try:
            self.ftp = FTP()
            self.ftp.connect(ip, port, timeout=10)
            self.ftp.login(user, password)
            self.su_anki_dizin = "/"
            messagebox.showinfo("Başarılı", f"{ip} sunucusuna bağlanıldı!")
            self.dosyalari_listele()
        except Exception as e:
            messagebox.showerror("Bağlantı Hatası", f"Bağlanılamadı:\n{e}")

    def dosyalari_listele(self):
        if not self.ftp:
            return
        
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.lbl_path.config(text=self.su_anki_dizin)

        try:
            self.ftp.cwd(self.su_anki_dizin)
            
            veri = []
            self.ftp.retrlines('LIST', veri.append)

            sira = 0
            for satir in veri:
                parcalar = satir.split(None, 8)
                if len(parcalar) < 9:
                    continue
                izinler = parcalar[0]
                isim = parcalar[8]

                if isim in ['.', '..']:
                    continue

                if izinler.startswith('d'):
                    tur = " 📁 Klasör"
                else:
                    tur = " 📄 Dosya"
                
                tag = 'cift' if sira % 2 == 0 else 'tek'
                self.tree.insert("", "end", values=(tur, isim), tags=(tag,))
                sira += 1

        except Exception as e:
            messagebox.showerror("Hata", f"Dizin listelenemedi:\n{e}")

    def klasore_gir_veya_calistir(self, event):
        secili_item = self.tree.selection()
        if not secili_item:
            return
        
        degerler = self.tree.item(secili_item, "values")
        tur = degerler[0]
        isim = degerler[1]

        if "Klasör" in tur:
            if self.su_anki_dizin.endswith("/"):
                self.su_anki_dizin += isim
            else:
                self.su_anki_dizin += "/" + isim
            self.dosyalari_listele()

    def ust_klasore_cik(self):
        if not self.ftp or self.su_anki_dizin == "/":
            return
        
        parcalar = self.su_anki_dizin.rstrip("/").split("/")
        parcalar.pop()
        self.su_anki_dizin = "/" + "/".join(parcalar) if parcalar else "/"
        self.dosyalari_listele()

    def dosya_yukle(self):
        if not self.ftp:
            messagebox.showwarning("Uyarı", "Önce bağlanmalısın!")
            return

        dosya_yolu = filedialog.askopenfilename()
        if dosya_yolu:
            dosya_adi = os.path.basename(dosya_yolu)
            try:
                self.ftp.cwd(self.su_anki_dizin)
                with open(dosya_yolu, "rb") as f:
                    self.ftp.storbinary(f"STOR {dosya_adi}", f)
                messagebox.showinfo("Başarılı", f"'{dosya_adi}' yüklendi!")
                self.dosyalari_listele()
            except Exception as e:
                messagebox.showerror("Hata", f"Yükleme hatası:\n{e}")

    def dosya_indir(self):
        if not self.ftp:
            messagebox.showwarning("Uyarı", "Önce bağlanmalısın!")
            return

        secili_item = self.tree.selection()
        if not secili_item:
            messagebox.showwarning("Uyarı", "Dosya seçmelisin!")
            return

        degerler = self.tree.item(secili_item, "values")
        tur = degerler[0]
        dosya_adi = degerler[1]

        if "Klasör" in tur:
            messagebox.showwarning("Uyarı", "Klasörler doğrudan indirilemez, içine girip dosyaları seçebilirsin.")
            return

        kayit_yolu = filedialog.asksaveasfilename(initialfile=dosya_adi)
        if kayit_yolu:
            try:
                self.ftp.cwd(self.su_anki_dizin)
                with open(kayit_yolu, "wb") as f:
                    self.ftp.retrbinary(f"RETR {dosya_adi}", f.write)
                messagebox.showinfo("Başarılı", f"İndirildi!")
            except Exception as e:
                messagebox.showerror("Hata", f"İndirme hatası:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FTPClientApp(root)
    root.mainloop()
