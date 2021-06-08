# Customer Segmention using RFM
# Mevcut müşterilerimizin satın alma davranışlarını göz önünde bulundurarak RFM analizi ile müşterilerimizi segmentlere ayırıp onlar için özel kararlar alıcaz.

# Değişkenler
# InvoiceNo: Fatura Numarası , Eğer bu kod C ile başlıyorsa işlemin iptal edildiğini ifade eder.
# StockCode: Ürün kodu, Her bir ürün için eşsiz numara.
# Description: Ürün İsmi
# Quantity: Ürün Adedi, Faturlardaki ürünlerden kaçar tane satıldığını ifade etmektedir.
# InvoiceDate: Fatura Tarihi
# UnitPrice: Fatura fiyatı(sterlin)
# CustomerID: Eşsiz müşteri numarası
# Country: Ülke ismi

# Gerekli olan kütüphaneleri import ediyoruz.
import datetime as dt
import pandas as pd

pd.set_option('display.max_columns', None)                    # bütün sutun isimlerini eksizsiz gösterir.
pd.set_option('display.max_rows', None)                       # veri setindeki değişkenleri yan yana yazdırır.
pd.set_option('display.float_format', lambda x: '%.2f' % x)   # virgülden sonra kaç basamak sayı gösterilmesi için.

df = pd.read_excel("datasets/online_retail_II.xlsx", sheet_name="Year 2010-2011")
retail = df.copy()

###############################################################
# Veri setinin yapısal bilgilerinin incelenmesi:
###############################################################
def check_df(dataframe, head=5):
    print(" - Tip Bilgisi - ".upper().center(50, "*"))
    print(dataframe.dtypes)
    print(" - Satır ve Sütun Sayısı - ".upper().center(50, "*"))
    print(dataframe.shape)
    print(" - Toplam Eleman Sayısı - ".upper().center(50, "*"))
    print(dataframe.size)
    print(" - Toplam Boyut - ".upper().center(50, "*"))
    print(dataframe.ndim)
    print(" - İlk 5 Gözlem - ".upper().center(50, "*"))
    print(dataframe.head(head))
    print(" - Son 5 Gözlem - ".upper().center(50, "*"))
    print(dataframe.tail(head))
    print(" - info - ".upper().center(50, "*"))
    dataframe.info()
    print(" - Boş Gözleme Sahip Değişkenler - ".upper().center(50, "*"))
    print(dataframe.isnull().sum())
    print(" - describe - ".upper().center(50, "*"))
    print(dataframe.describe().T)
check_df(retail)

retail.dropna(inplace=True)   # Eksik gözlemlerin kalıcı olarak silinme işlemi.

# Eşsiz ürün sayısı?
retail["Description"].nunique()

# Hangi üründen kaçar tane mevcut?
retail["Description"].value_counts()

# En çok sipariş edilen 5 ürünü çoktan aza doğru
retail.groupby("Description", as_index=False).agg({"Quantity":"sum"}).sort_values(by = "Quantity" , ascending = False).head()

# En çok ürün sipariş eden 5 ülkeyi çoktan aza doğru
retail.groupby("Country", as_index=False).agg({"Quantity": "sum"}).sort_values(by = "Quantity" , ascending = False).head()

# Faturalardaki 'C' iptal edilen işlemleri veri setinden çıkarma işlemi:
retail = retail[~retail["Invoice"].str.contains("C", na=False)]
retail.head()

retail["TotalPrice"] = retail["Quantity"] * retail["Price"]     # her bir faturanın toplam bedeli

###############################################################
# RFM metriklerinin hesaplanması
###############################################################
"""
Recency (yenilik): Müşterinin ne kadar süredir websitesinden/mağazadan vb. hizmet aldığı, ne zamandır bize üye olduğu gibi bilgileri verir. Hesaplanma şekli çoğunlukla müşterinin en son alışveriş yaptığı tarihten bugüne kadar olan zamanın çıkartılmasıyla elde edilir.

Frequency (Sıklık): Genellikle sipariş numarası ya da sipariş kodunun saydırılmasıyla sonuç verir. Aslında müşterinin ne sıklıkla alışveriş yaptığını, ne sıklıkla siteye giriş yaptığını gösteren metriktir. 

Monetary (Parasal Değer): Müşterinin yaptığı harcamalarının toplamıdır. Örneğin; E-ticaret sitesine getirdiği ciro, yani toplam getiri
"""

retail["InvoiceDate"].max()   # En son fatura tarihini bulma.

today_date = dt.datetime(2011, 12, 11)  # 2 gün sonrasını aldık garanti olsun.

rfm = retail.groupby('Customer ID').agg({'InvoiceDate': lambda date: (today_date - date.max()).days,
                                     'Invoice': lambda num: num.nunique(),
                                     'TotalPrice': lambda TotalPrice: TotalPrice.sum()})

rfm.head()
rfm.columns = ['recency', 'frequency', 'monetary']   # kolon isimlerini değiştirme
rfm.head()

rfm.describe().T

# Frequency 0'dan büyük olduğu halde monetary'e yansımamış bir işlem var demek oluyor. Filtreleme yapmalıyız.
rfm = rfm[rfm["monetary"] > 0]

# Recency, Frequency ve monetary metriklerini qcut yardımı ile 1-5 arasında skorlara çevirme işlemi için:
# Küçükten büyüğe doğru sıralar ve küçük olan değere büyük skor mantığı ile.
rfm["recency_score"] = pd.qcut(rfm['recency'], 5, labels=[5, 4, 3, 2, 1])

# Küçük olana küçük skor ve rank ile ilk yakaladığını seçer.
rfm["frequency_score"] = pd.qcut(rfm['frequency'].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])

# Frequency gibi küçük olana küçük, büyük olana büyük skor.
rfm["monetary_score"] = pd.qcut(rfm['monetary'], 5, labels=[1, 2, 3, 4, 5])

# Oluşan 3 farklı değişkenin değerini tek bir değişken olarak ifade edilmesi:
# Monetary_score almadım çünkü bizim için müşteri teması önemli, monetary'e pekte gerek yok
rfm["RFM_SCORE"] = (rfm['recency_score'].astype(str) + rfm['frequency_score'].astype(str))

rfm.describe().T

rfm[rfm["RFM_SCORE"] == "55"].head()  # champions

rfm[rfm["RFM_SCORE"] == "11"].head()  # hibernating

###############################################################
# RFM skorlarının segment olarak tanımlanması
###############################################################
seg_map = {
    r'[1-2][1-2]': 'hibernating',
    r'[1-2][3-4]': 'at_Risk',
    r'[1-2]5': 'cant_loose',
    r'3[1-2]': 'about_to_sleep',
    r'33': 'need_attention',
    r'[3-4][4-5]': 'loyal_customers',
    r'41': 'promising',
    r'51': 'new_customers',
    r'[4-5][2-3]': 'potential_loyalists',
    r'5[4-5]': 'champions'
}

# regular expression ile uygulayarak gerçekleşti.
rfm['segment'] = rfm['RFM_SCORE'].replace(seg_map, regex=True)  # birleştirilen skorlar seg_map ile değiştirildi
rfm.head()

# En başta oluşturduğum metrikleri seçtim, segmentlere göre skorların ortalamalarını ve countlarını aldım.
rfm[["segment", "recency", "frequency", "monetary"]].groupby("segment").agg(["mean", "count"])

# Seçilen segmentleri gözlemlemek için:
list = ['at_Risk', 'hibernating', 'cant_loose', 'loyal_customers']
for i in list:
    print(F" {i.upper()} ".center(50, "*"))
    print(rfm[rfm["segment"]==i].describe().T)

new_df = pd.DataFrame()
# Dikkate gerektiren sınıfların id'lerini aldık. çünkü indexlerde id'ler vardı.
new_df["loyal_customers_id"] = rfm[rfm["segment"] == "loyal_customers"].index
new_df.head()

new_df.to_excel("HAFTA_03/loyal_customers.xlsx")

##################################################################################################
# TKİNTER EKRANINA SEGMENTLERİN BAR PLOT İLE ÇİZMİNİN AKTARILMASI
##################################################################################################
import datetime as dt
import pandas as pd

import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

master = tk.Tk()
w = master.winfo_screenwidth()
h = master.winfo_screenheight()
master.geometry("%dx%d" % (w, h))

def create_rfm(dataframe):

    # VERİNİN HAZIRLANMA SÜRECİ
    dataframe["TotalPrice"] = dataframe["Quantity"] * dataframe["Price"]
    dataframe.dropna(inplace=True)
    dataframe = dataframe[~dataframe["Invoice"].str.contains("C", na=False)]

    # RFM METRIKLERININ HESAPLANMASI
    today_date = dt.datetime(2011, 12, 11)
    rfm = dataframe.groupby('Customer ID').agg({'InvoiceDate': lambda date: (today_date - date.max()).days,
                                                'Invoice': lambda num: num.nunique(),
                                                "TotalPrice": lambda price: price.sum()})
    rfm.columns = ['recency', 'frequency', "monetary"]
    rfm = rfm[(rfm['monetary'] > 0)]

    # RFM SKORLARININ HESAPLANMASI
    rfm["recency_score"] = pd.qcut(rfm['recency'], 5, labels=[5, 4, 3, 2, 1])
    rfm["frequency_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
    rfm["monetary_score"] = pd.qcut(rfm['monetary'], 5, labels=[1, 2, 3, 4, 5])

    # Değişkenler str haline dönüştürülüp birleştirildi
    rfm["RFM_SCORE"] = (rfm['recency_score'].astype(str) +
                        rfm['frequency_score'].astype(str))


    # SEGMENTLERIN ISIMLENDIRILMESI
    seg_map = {
        r'[1-2][1-2]': 'hibernating',
        r'[1-2][3-4]': 'at_risk',
        r'[1-2]5': 'cant_loose',
        r'3[1-2]': 'about_to_sleep',
        r'33': 'need_attention',
        r'[3-4][4-5]': 'loyal_customers',
        r'41': 'promising',
        r'51': 'new_customers',
        r'[4-5][2-3]': 'potential_loyalists',
        r'5[4-5]': 'champions'
    }

    rfm['segment'] = rfm['RFM_SCORE'].replace(seg_map, regex=True)
    rfm = rfm[["recency", "frequency", "monetary", "segment"]]
    return rfm

df = pd.read_excel("datasets/online_retail_II.xlsx", sheet_name="Year 2010-2011")
df_ = df.copy()
rfm_new = create_rfm(df_)
rfm_new.head()

def plts():
    fig, a3 = plt.subplots(figsize=(8,9))
    rfm_new['segment'].value_counts().plot(kind='bar', rot=100, fontsize=7)
    plt.title('SEGMENTS', fontsize=15, y=1.03)
    plt.ylabel('Count', fontsize=15)
    plt.show()

    canvas = FigureCanvasTkAgg(fig, master=master)
    canvas.get_tk_widget().place(x=100,y=65)
    canvas.draw()
    plt.close("all")


label1 = tk.Label(master, text='RFM CUSTOMER SEGMENTION',fg="Red", font=("Helvetica", 25))
label1.place(x=125, y=20)

d = tk.Button(master, text="RUN", command=plts)
d.place(x=20,y=400)

master.mainloop()



