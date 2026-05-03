# Rule Sistem Analisis Klasterisasi Faktor Risiko Oligohydramnion
## Menggunakan Metode Fuzzy C-Means (FCM)
### RSU Srikandi IBI Jember

---

## 1. GAMBARAN UMUM SISTEM

Sistem ini dirancang untuk mengklasterisasi faktor risiko oligohydramnion pada ibu hamil menggunakan algoritma **Fuzzy C-Means (FCM)**. Terdapat **3 proses utama**:

1. **Preprocessing** – Transformasi & Normalisasi Data
2. **Training** – Proses iterasi FCM hingga konvergen
3. **Testing** – Pengujian data baru
4. **Validasi Partition Coefficient (PC)** – Evaluasi kualitas klaster & prediksi tindakan

---

## 2. STRUKTUR DATA INPUT

### 2.1 Format Data Pasien (CSV Input)

| Kolom               | Tipe    | Keterangan                                        |
|---------------------|---------|---------------------------------------------------|
| No                  | Integer | Nomor urut                                        |
| Nomor RM            | String  | Nomor rekam medis pasien                          |
| Usia Ibu            | Integer | Usia ibu dalam tahun                              |
| Usia Kehamilan      | Integer | Usia kehamilan dalam minggu                       |
| Gravida             | Integer | Jumlah kehamilan (angka asli)                     |
| Tekanan Darah       | String  | Format: `sistolik/diastolik` mmHg (contoh: 120/80)|
| Denyut Jantung Janin| Integer | DJJ dalam BPM                                     |
| Nilai AFI           | Float   | Amniotic Fluid Index dalam cm                     |
| Kejadian KPD        | String  | `"ada"` atau `"tidak"` (Ketuban Pecah Dini)       |
| Tindakan            | String  | Label tindakan medis (sc, sc+mow, dll.)           |

### 2.2 Contoh Data Sebelum Preprocessing

```
No, Nomor RM, Usia Ibu, Usia Kehamilan, Gravida, Tekanan Darah, Denyut Jantung Janin, Nilai AFI, Kejadian KPD, Tindakan
1,  054121,   29,       37,             2,       120/80,         148,                  3,         tidak,         sc
2,  065046,   27,       38,             2,       110/70,         139,                  3,         tidak,         sc
3,  078533,   33,       37,             2,       100/70,         136,                  3,         tidak,         sc
4,  083531,   22,       38,             1,       120/80,         141,                  3,         tidak,         sc
5,  079120,   36,       35,             3,       120/80,         149,                  2,         ada,           sc+mow
```

---

## 3. PROSES PREPROCESSING

### 3.1 Transformasi Atribut Gravida

| Nilai Asli (Gravida) | Nilai Atribut | Label       |
|----------------------|---------------|-------------|
| = 1                  | 1             | Primigravida|
| > 1                  | 2             | Multigravida|

**Aturan:**
```
IF gravida == 1 THEN atribut_gravida = 1  (Primigravida)
IF gravida > 1  THEN atribut_gravida = 2  (Multigravida)
```

### 3.2 Transformasi Atribut Tekanan Darah

Tekanan darah diambil dari kolom format `sistolik/diastolik` mmHg.

| Kondisi                                      | Nilai Atribut | Label              |
|----------------------------------------------|---------------|--------------------|
| Normal: sistolik < 140 DAN diastolik < 90    | 1             | Normal             |
| Hipertensi Ringan: sistolik ≥ 140 ATAU diastolik ≥ 90 | 2    | Hipertensi Ringan  |
| Hipertensi Berat: sistolik 160–180 mmHg      | 3             | Hipertensi Berat   |

**Aturan:**
```
IF sistolik < 140 AND diastolik < 90        THEN atribut_td = 1  (Normal)
ELIF sistolik >= 140 OR diastolik >= 90     THEN atribut_td = 2  (Hipertensi Ringan)
ELIF sistolik >= 160 AND sistolik <= 180    THEN atribut_td = 3  (Hipertensi Berat)
```

### 3.3 Transformasi Atribut Denyut Jantung Janin (DJJ)

| Kondisi DJJ                 | Nilai Atribut | Label       |
|-----------------------------|---------------|-------------|
| Normal: 120 – 160 BPM       | 0             | Normal      |
| Takikardia: > 160 BPM       | 1             | Takikardia  |
| Bradikardia: < 120 BPM      | 2             | Bradikardia |

### 3.4 Transformasi Atribut Kejadian KPD

| Nilai Asli | Nilai Atribut |
|------------|---------------|
| tidak      | 1             |
| ada        | 0             |

### 3.5 Normalisasi Data (Min-Max Normalization)

Setelah transformasi atribut, semua fitur dinormalisasi menggunakan **Min-Max Normalization** ke rentang [0, 1]:

$$x' = \frac{x - x_{min}}{x_{max} - x_{min}}$$

**Fitur yang dinormalisasi:**
- Usia Ibu
- Usia Kehamilan
- Gravida (setelah transformasi)
- Tekanan Darah (setelah transformasi)
- Denyut Jantung Janin (setelah transformasi)
- Nilai AFI
- Kejadian KPD (setelah transformasi)

### 3.6 Contoh Output Setelah Preprocessing

```
No, Nomor RM, Usia Ibu, Usia Kehamilan, Gravida, Tekanan Darah, Denyut Jantung Janin, Nilai AFI, Kejadian KPD
1,  054121,   29,       37,             2,       1,              0,                    3,         1
2,  065046,   27,       38,             2,       1,              0,                    3,         1
3,  078533,   33,       37,             2,       1,              0,                    3,         1
4,  083531,   22,       38,             1,       1,              0,                    3,         1
5,  079120,   36,       35,             2,       1,              0,                    2,         0
```

> **Catatan:** Kolom `Tindakan` dihapus dari output preprocessing (digunakan hanya sebagai label referensi validasi).

---

## 4. PROSES TRAINING – ALGORITMA FUZZY C-MEANS

### 4.1 Parameter FCM

| Parameter        | Nilai           | Keterangan                                    |
|------------------|-----------------|-----------------------------------------------|
| c                | 3               | Jumlah klaster (Mild, Moderate, Severe)       |
| m                | 2               | Fuzzy weighting exponent (fuzzifier)          |
| ε (epsilon)      | 0.0001          | Threshold konvergensi (max selisih)           |
| Max Iterasi      | 100             | Batas maksimum iterasi                        |
| Inisialisasi     | Random          | Matriks keanggotaan awal (U₀)                 |

### 4.2 Algoritma FCM Step-by-Step

#### STEP 1 – Inisialisasi Matriks Keanggotaan (U)

Inisialisasi matriks partisi fuzzy U secara random dengan syarat:

$$\sum_{k=1}^{c} \mu_{ik} = 1, \quad \forall i = 1, \ldots, n$$

dimana:
- $\mu_{ik}$ = derajat keanggotaan data ke-$i$ pada klaster ke-$k$
- $n$ = jumlah data
- $c$ = jumlah klaster (3)

#### STEP 2 – Hitung Pusat Klaster (Cluster Center / V)

$$v_{kj} = \frac{\sum_{i=1}^{n} (\mu_{ik})^m \cdot x_{ij}}{\sum_{i=1}^{n} (\mu_{ik})^m}$$

dimana:
- $v_{kj}$ = pusat klaster ke-$k$ untuk fitur ke-$j$
- $x_{ij}$ = nilai fitur ke-$j$ dari data ke-$i$
- $m$ = fuzzifier (= 2)

**Contoh formula pusat klaster (Klaster 1, fitur Usia Ibu):**

$$v_{1, \text{Usia Ibu}} = \frac{\sum_{i=1}^{n} (\mu_{i1})^2 \cdot x_{i, \text{Usia Ibu}}}{\sum_{i=1}^{n} (\mu_{i1})^2}$$

#### STEP 3 – Hitung Jarak Euclidean (D)

$$d_{ik} = \sqrt{\sum_{j=1}^{p} (x_{ij} - v_{kj})^2}$$

dimana:
- $d_{ik}$ = jarak data ke-$i$ ke pusat klaster ke-$k$
- $p$ = jumlah fitur (7)

#### STEP 4 – Update Matriks Keanggotaan (U)

$$\mu_{ik} = \frac{1}{\sum_{l=1}^{c} \left(\frac{d_{ik}}{d_{il}}\right)^{\frac{2}{m-1}}}$$

#### STEP 5 – Cek Konvergensi

$$\max |U^{(t+1)} - U^{(t)}| < \varepsilon$$

Jika belum konvergen, kembali ke STEP 2.

---

## 5. PROSES TESTING

### 5.1 Input Testing
Data testing menggunakan data baru yang melalui proses preprocessing yang sama.

### 5.2 Proses Klasterisasi Data Testing
1. Gunakan pusat klaster **V** hasil training terakhir
2. Hitung jarak Euclidean data testing ke setiap pusat klaster
3. Hitung derajat keanggotaan (μ) menggunakan formula UPDATE
4. Tentukan klaster berdasarkan nilai μ tertinggi

---

## 6. VALIDASI PARTITION COEFFICIENT (PC)

### 6.1 Formula Partition Coefficient

$$PC = \frac{1}{n} \sum_{i=1}^{n} \sum_{k=1}^{c} (\mu_{ik})^2$$

dimana:
- $PC \in [1/c, 1]$
- Nilai PC mendekati 1 = klasterisasi sangat baik
- Nilai PC mendekati $1/c$ = klasterisasi buruk (overlap tinggi)

### 6.2 Interpretasi Nilai PC

| Rentang PC      | Kualitas Klasterisasi |
|-----------------|----------------------|
| 0.80 – 1.00     | Sangat Baik          |
| 0.60 – 0.79     | Baik                 |
| 0.40 – 0.59     | Cukup                |
| < 0.40          | Buruk                |

---

## 7. DEFINISI KLASTER & TINGKAT KEPARAHAN

### 7.1 Klaster 1 – MILD (Ringan)

**Karakteristik:**
- AFI: 4.1 – 5.0 cm
- Tekanan Darah: Normal (< 140/90 mmHg) → atribut = 1
- DJJ: Normal (120–160 BPM) → atribut = 0

**Saran Tindakan Medis:**
- Manajemen konservatif (bed rest / tirah baring)
- Rehidrasi maternal (oral/intravena)
- Persalinan spontan pervaginam dengan pemantauan ketat
- Monitor AFI berkala

### 7.2 Klaster 2 – MODERATE (Sedang)

**Karakteristik:**
- AFI: 2.1 – 4.0 cm
- Tekanan Darah: mulai meningkat (bisa normal atau hipertensi ringan)
- DJJ: bisa normal atau mulai tidak stabil

**Saran Tindakan Medis:**
- Sectio Caesarea (SC) atau SCTP (Sectio Caesarea Transperitoneal Profunda)
- SCTP direkomendasikan karena risiko perdarahan lebih rendah
- Pertimbangkan tambahan MOW (Metode Operasi Wanita/Tubektomi) jika:
  - Usia ibu > 35 tahun
  - Gravida ≥ 3

### 7.3 Klaster 3 – SEVERE (Berat)

**Karakteristik:**
- AFI: 0 – 2.0 cm
- Tekanan Darah: Hipertensi (≥ 140/90 mmHg) → atribut = 2 atau 3
- DJJ: Takikardia (> 160 BPM) → atribut = 1

**Saran Tindakan Medis:**
- **SC Cito** atau **SCTP Darurat** (terminasi segera)
- Indikasi: kombinasi AFI kritis + hipertensi + gawat janin
- Tambahan **MOW (Tubektomi)** jika:
  - Usia ibu > 37 tahun
  - Gravida ≥ 3
  - Risiko kehamilan berikutnya sangat tinggi

---

## 8. SPESIFIKASI OUTPUT FILE

### 8.1 Output 1 – Hasil Preprocessing (`output_preprocessing.csv`)

**Format Tabel:**

| No | Nomor RM | Usia Ibu | Usia Kehamilan | Gravida | Tekanan Darah | Denyut Jantung Janin | Nilai AFI | Kejadian KPD |
|----|----------|----------|----------------|---------|---------------|----------------------|-----------|--------------|

> Kolom `Tindakan` tidak disertakan.

---

### 8.2 Output 2 – Hasil Perhitungan Setiap Iterasi (`output_iterasi.csv`)

**Format Tabel:**

| No | Nomor RM | K1 | K2 | K3 | Max Selisih |
|----|----------|----|----|----|-------------|

**Keterangan:**
- K1, K2, K3 = nilai derajat keanggotaan (μ) ke klaster 1, 2, 3 pada iterasi tersebut
- Max Selisih = nilai maksimum perubahan matriks U antara iterasi $t$ dan $t+1$

> File ini di-generate untuk **setiap iterasi** hingga konvergen. Nama file disarankan: `output_iterasi_t{nomor_iterasi}.csv`

---

### 8.3 Output 3 – Update Nilai Keanggotaan Baru (`output_keanggotaan.csv`)

**Format Tabel:**

| No | Nomor RM | μ1 | μ2 | μ3 |
|----|----------|----|----|----|

**Keterangan:**
- μ1, μ2, μ3 = nilai keanggotaan (membership degree) terbaru setiap data terhadap klaster 1, 2, 3
- Diambil dari hasil iterasi **terakhir** (setelah konvergen)

---

### 8.4 Output 4 – Hasil Jarak Euclidean (`output_euclidean.csv`)

**Format Tabel:**

| No | Nomor RM | d1 | d2 | d3 |
|----|----------|----|----|----|

**Keterangan:**
- d1, d2, d3 = jarak Euclidean setiap data ke pusat klaster 1, 2, 3
- Menggunakan simbol header: `μ1`, `μ2`, `μ3` (sesuai permintaan)

---

### 8.5 Output 5 – Hasil Hitung Pusat Klaster (`output_pusat_klaster.csv`)

**Format Tabel:**

| Klaster | Usia Ibu | Usia Kehamilan | Gravida | Tekanan Darah | Denyut Jantung Janin | Nilai AFI | Kejadian KPD |
|---------|----------|----------------|---------|---------------|----------------------|-----------|--------------|

**Keterangan:**
- Berisi 3 baris (satu untuk setiap klaster: K1=Mild, K2=Moderate, K3=Severe)
- Nilai adalah **pusat klaster final** setelah konvergen

---

### 8.6 Output 6 – Hasil Perhitungan Partition Coefficient (`output_partition_coefficient.csv`)

**Format Tabel:**

| No | Nomor RM | K1 | K2 | K3 |
|----|----------|----|----|----|

**Keterangan:**
- K1, K2, K3 = nilai $(\mu_{ik})^2$ (kuadrat keanggotaan) untuk setiap klaster
- Nilai PC global = rata-rata total dari semua $(\mu_{ik})^2$

---

### 8.7 Output 7 – Hasil FCM Final (`output_fcm_final.csv`)

**Format Tabel:**

| No | Nomor RM | K1 | K2 | K3 | μ1² | μ2² | μ3² | Hasil |
|----|----------|----|----|----|-----|-----|-----|-------|

**Keterangan:**
- K1, K2, K3 = derajat keanggotaan akhir (μ1, μ2, μ3)
- μ1², μ2², μ3² = kuadrat dari nilai keanggotaan (digunakan untuk PC)
- Hasil = label klaster dominan: **Mild** / **Moderate** / **Severe** (berdasarkan nilai μ tertinggi)

---

### 8.8 Output 8 – Perhitungan Pusat Klaster Format TXT (`output_pusat_klaster_K{n}.txt`)

**Deskripsi:**  
File TXT yang menampilkan detail perhitungan pusat klaster dalam format matematika lengkap, seperti pada gambar referensi. Dibuat untuk **setiap klaster** (K1, K2, K3).

**Format isi file:**

```
Klaster [N] [LABEL]

(μ_i1^m × x_i1) + (μ_i2^m × x_i2) + ... + (μ_in^m × x_in)
V_kj = ──────────────────────────────────────────────────────────
        μ_i1^m + μ_i2^m + ... + μ_in^m

     = [nilai numerator (pembilang, penjumlahan perkalian μ² × x)]
       ──────────────────────────────────────────────────────────
       [nilai denominator (penyebut, penjumlahan μ²)]

     = [hasil akhir per fitur]
```

**Contoh format output TXT (mengacu pada gambar referensi):**

```
Klaster 1 BB

/ (μ₁₁² × x₁₁) + (μ₂₁² × x₂₁) + ... \
|                                        |
|    (pembilang lengkap semua data)      |
|                                        |
\ (semua penjumlahan di baris numerator) /
= ──────────────────────────────────────── ^ (1/m-1)
/ μ₁₁² + μ₂₁² + ... + μ_n1²            \
|                                         |
|    (penyebut lengkap semua data)        |
|                                         |
\ (semua penjumlahan di baris denominator)/
```

**Nama file output:**
- `output_pusat_klaster_K1.txt` → Klaster 1 (Mild)
- `output_pusat_klaster_K2.txt` → Klaster 2 (Moderate)  
- `output_pusat_klaster_K3.txt` → Klaster 3 (Severe)

**Isi file TXT memuat perhitungan untuk setiap fitur:**
1. Usia Ibu
2. Usia Kehamilan
3. Gravida
4. Tekanan Darah
5. Denyut Jantung Janin
6. Nilai AFI
7. Kejadian Ketuban Pecah Dini

---

## 9. ALUR SISTEM LENGKAP (FLOWCHART LOGIS)

```
[INPUT: Data Pasien CSV]
          │
          ▼
┌─────────────────────────────────────────────────────┐
│                   PREPROCESSING                      │
│  1. Transformasi Gravida (1→Primigravida, >1→Multi)  │
│  2. Transformasi Tekanan Darah (1=Normal, 2=HT      │
│     Ringan, 3=HT Berat)                              │
│  3. Transformasi DJJ (0=Normal, 1=Takikardia)        │
│  4. Transformasi KPD (tidak=1, ada=0)                │
│  5. Min-Max Normalisasi semua fitur ke [0,1]         │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼ output_preprocessing.csv
┌─────────────────────────────────────────────────────┐
│                     TRAINING FCM                     │
│  1. Inisialisasi matriks U (random, sum=1)           │
│  2. Hitung pusat klaster V                           │
│  3. Hitung jarak Euclidean D                         │
│  4. Update matriks keanggotaan U baru               │
│  5. Cek konvergensi (max selisih < ε)                │
│  6. Jika belum konvergen → ulang dari step 2        │
└───────────────────────┬─────────────────────────────┘
                        │ output per iterasi:
                        │ - output_iterasi_t{n}.csv
                        │ - output_keanggotaan.csv
                        │ - output_euclidean.csv
                        │ - output_pusat_klaster.csv
                        │ - output_pusat_klaster_K{n}.txt
                        ▼
┌─────────────────────────────────────────────────────┐
│                      TESTING                         │
│  1. Input data baru → preprocessing                  │
│  2. Hitung jarak ke pusat klaster V (dari training) │
│  3. Hitung derajat keanggotaan μ                     │
│  4. Tentukan klaster dominan (μ tertinggi)           │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│           VALIDASI PARTITION COEFFICIENT             │
│  1. Hitung PC = (1/n) Σ Σ μ²_ik                     │
│  2. Evaluasi kualitas klaster                        │
│  3. Prediksi tindakan medis per klaster:             │
│     - K1 (Mild)    → Konservatif/Pervaginam          │
│     - K2 (Moderate)→ SC / SCTP (± MOW)              │
│     - K3 (Severe)  → SC Cito / SCTP Darurat (± MOW) │
└───────────────────────┬─────────────────────────────┘
                        │ output:
                        │ - output_partition_coefficient.csv
                        │ - output_fcm_final.csv
                        ▼
               [OUTPUT AKHIR + REKOMENDASI TINDAKAN]
```

---

## 10. ATURAN PREDIKSI TINDAKAN MEDIS

### 10.1 Logika Prediksi Berdasarkan Klaster + Kondisi Pasien

```python
def prediksi_tindakan(klaster, usia_ibu, gravida, tekanan_darah_atribut):
    """
    klaster         : 1=Mild, 2=Moderate, 3=Severe
    usia_ibu        : usia dalam tahun (nilai asli)
    gravida         : nilai asli gravida
    tekanan_darah_atribut : 1=Normal, 2=HT Ringan, 3=HT Berat
    """
    tindakan = ""
    
    if klaster == 1:  # MILD
        tindakan = "Observasi, Bed Rest, Rehidrasi, Pervaginam"
    
    elif klaster == 2:  # MODERATE
        tindakan = "SC / SCTP"
        if usia_ibu > 35 and gravida >= 3:
            tindakan += " + MOW"
    
    elif klaster == 3:  # SEVERE
        tindakan = "SC Cito / SCTP Darurat"
        if usia_ibu > 37 and gravida >= 3:
            tindakan += " + MOW"
    
    return tindakan
```

### 10.2 Tabel Ringkasan Prediksi Tindakan

| Klaster  | Tingkat Keparahan | AFI (cm)   | Tindakan Utama                     | Kondisi Tambahan MOW               |
|----------|-------------------|------------|------------------------------------|------------------------------------|
| K1       | Mild              | 4.1 – 5.0  | Observasi, Bed Rest, Rehidrasi, Pervaginam | -                         |
| K2       | Moderate          | 2.1 – 4.0  | SC / SCTP                          | Usia > 35 tahun AND Gravida ≥ 3   |
| K3       | Severe            | 0 – 2.0    | SC Cito / SCTP Darurat             | Usia > 37 tahun AND Gravida ≥ 3   |

---

## 11. CATATAN TEKNIS IMPLEMENTASI

### 11.1 Library Python yang Disarankan
```
pandas          - manipulasi data CSV
numpy           - komputasi matriks FCM
scikit-fuzzy    - implementasi FCM (skfuzzy.cluster.cmeans)
matplotlib      - visualisasi klaster (opsional)
```

### 11.2 Format Penamaan File Output

| No  | Nama File                         | Deskripsi                                      |
|-----|-----------------------------------|------------------------------------------------|
| 1   | `output_preprocessing.csv`        | Data setelah transformasi & normalisasi        |
| 2   | `output_iterasi_t{n}.csv`         | Nilai keanggotaan per iterasi (n = nomor iter) |
| 3   | `output_keanggotaan.csv`          | Nilai keanggotaan final (μ1, μ2, μ3)           |
| 4   | `output_euclidean.csv`            | Jarak Euclidean ke setiap pusat klaster        |
| 5   | `output_pusat_klaster.csv`        | Koordinat pusat klaster per fitur              |
| 6   | `output_pusat_klaster_K1.txt`     | Detail perhitungan pusat Klaster 1 (Mild)      |
| 7   | `output_pusat_klaster_K2.txt`     | Detail perhitungan pusat Klaster 2 (Moderate)  |
| 8   | `output_pusat_klaster_K3.txt`     | Detail perhitungan pusat Klaster 3 (Severe)    |
| 9   | `output_partition_coefficient.csv`| Nilai PC per data (K1², K2², K3²)              |
| 10  | `output_fcm_final.csv`            | Hasil akhir FCM + label klaster + tindakan     |

### 11.3 Konvensi Nilai Keanggotaan
- Semua nilai μ berada di rentang **[0, 1]**
- Untuk setiap data: μ1 + μ2 + μ3 = **1.0**
- Klaster dominan = klaster dengan nilai μ **terbesar**
- Jika ada dua μ sama besar → pilih klaster dengan indeks lebih kecil

### 11.4 Format Angka dalam File Output
- Nilai μ: **6 desimal** (contoh: 0.296296)
- Nilai jarak Euclidean: **6 desimal**
- Nilai pusat klaster: **6 desimal**
- Nilai PC: **6 desimal**

---

## 12. REFERENSI FORMULA UTAMA

### 12.1 Ringkasan Formula FCM

| Tahap             | Formula                                                                                                    |
|-------------------|------------------------------------------------------------------------------------------------------------|
| Inisialisasi U    | $\mu_{ik} \in [0,1]$, $\sum_{k=1}^{c} \mu_{ik} = 1$                                                      |
| Pusat Klaster     | $v_{kj} = \frac{\sum_{i=1}^{n} \mu_{ik}^m x_{ij}}{\sum_{i=1}^{n} \mu_{ik}^m}$                           |
| Jarak Euclidean   | $d_{ik} = \sqrt{\sum_{j=1}^{p}(x_{ij} - v_{kj})^2}$                                                      |
| Update U          | $\mu_{ik} = \frac{1}{\sum_{l=1}^{c}\left(\frac{d_{ik}}{d_{il}}\right)^{\frac{2}{m-1}}}$                  |
| Konvergensi       | $\max \|U^{(t+1)} - U^{(t)}\| < \varepsilon$                                                              |
| Partition Coeff.  | $PC = \frac{1}{n}\sum_{i=1}^{n}\sum_{k=1}^{c} \mu_{ik}^2$                                                |

---

## 13. OUTPUT VISUALISASI

Seluruh visualisasi dibuat menggunakan library **matplotlib** dan **mpltern** (untuk Ternary Plot). Setiap plot disimpan sebagai file gambar PNG beresolusi tinggi di folder output.

---

### 13.1 Scatter Plot Clustering

**Nama File:** `visualisasi_scatter_plot.png`

**Deskripsi:**  
Menampilkan sebaran data pasien dalam ruang 2D berdasarkan dua fitur paling dominan (default: **Nilai AFI** vs **Usia Ibu**), diwarnai sesuai klaster dominan hasil FCM.

**Spesifikasi Plot:**
- Sumbu X: Nilai AFI (ternormalisasi)
- Sumbu Y: Usia Ibu (ternormalisasi)
- Warna titik: sesuai klaster dominan
  - 🔵 Biru = K1 Mild
  - 🟠 Oranye = K2 Moderate
  - 🔴 Merah = K3 Severe
- Marker pusat klaster (centroid): bintang (★) berukuran besar, warna hitam dengan border warna klaster
- Ukuran titik data: proporsional terhadap nilai μ tertinggi (semakin dominan = semakin besar)
- Judul: `"Scatter Plot Clustering FCM – Oligohydramnion"`
- Legend: K1 Mild, K2 Moderate, K3 Severe, Centroid

**Konten Tambahan:**
- Anotasi jumlah anggota tiap klaster: `"K1: n pasien"`, dll.
- Grid tipis untuk keterbacaan

**Kode Referensi:**
```python
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(10, 7))
colors = {1: '#40DF00', 2: '#FF9800', 3: '#F44336'}
labels = {1: 'K1 – Mild', 2: 'K2 – Moderate', 3: 'K3 – Severe'}

for k in [1, 2, 3]:
    idx = [i for i, d in enumerate(data) if dominant_cluster[i] == k]
    sizes = [mu_max[i] * 200 for i in idx]
    ax.scatter(data[idx, AFI_col], data[idx, USIA_col],
               c=colors[k], label=labels[k], s=sizes, alpha=0.8, edgecolors='white')

# Plot centroid
for k in [1, 2, 3]:
    ax.scatter(centroids[k-1, AFI_col], centroids[k-1, USIA_col],
               marker='*', s=400, c='black', edgecolors=colors[k], linewidths=2,
               zorder=5, label=f'Centroid K{k}')

ax.set_xlabel('Nilai AFI (ternormalisasi)')
ax.set_ylabel('Usia Ibu (ternormalisasi)')
ax.set_title('Scatter Plot Clustering FCM – Oligohydramnion')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('visualisasi_scatter_plot.png', dpi=150)
```

---

### 13.2 Membership Degree Plot

**Nama File:** `visualisasi_membership_degree.png`

**Deskripsi:**  
Menampilkan nilai derajat keanggotaan (μ1, μ2, μ3) setiap pasien terhadap ketiga klaster dalam bentuk **stacked bar chart horizontal**, sehingga mudah melihat distribusi keanggotaan fuzzy tiap data.

**Spesifikasi Plot:**
- Sumbu Y: Nomor RM pasien (urut dari atas ke bawah)
- Sumbu X: Nilai μ (0.0 – 1.0)
- Segmen bar:
  - 🔵 Biru = μ1 (Mild)
  - 🟠 Oranye = μ2 (Moderate)
  - 🔴 Merah = μ3 (Severe)
- Setiap bar total = 1.0 (karena μ1 + μ2 + μ3 = 1)
- Anotasi nilai μ di dalam segmen jika lebar segmen > 0.05
- Garis vertikal putus-putus pada x = 0.5 sebagai batas dominansi
- Judul: `"Membership Degree Plot – Derajat Keanggotaan Fuzzy per Pasien"`

**Informasi Tambahan:**
- Pasien dengan μ mendekati 1.0 pada satu klaster = anggota tegas
- Pasien dengan distribusi μ merata = "boundary case" yang perlu perhatian klinis lebih

**Kode Referensi:**
```python
fig, ax = plt.subplots(figsize=(12, max(6, len(data) * 0.4)))
rm_labels = [str(rm) for rm in nomor_rm]
colors = ['#40DF00', '#FF9800', '#F44336']
labels = ['μ1 Mild', 'μ2 Moderate', 'μ3 Severe']

left = np.zeros(len(data))
for k in range(3):
    bars = ax.barh(rm_labels, U[k], left=left, color=colors[k], label=labels[k], edgecolor='white')
    for bar, val in zip(bars, U[k]):
        if val > 0.05:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2,
                    f'{val:.3f}', ha='center', va='center', fontsize=7, color='white', fontweight='bold')
    left += U[k]

ax.axvline(x=0.5, color='black', linestyle='--', alpha=0.5, linewidth=1)
ax.set_xlabel('Derajat Keanggotaan (μ)')
ax.set_title('Membership Degree Plot – Derajat Keanggotaan Fuzzy per Pasien')
ax.legend(loc='lower right')
plt.tight_layout()
plt.savefig('visualisasi_membership_degree.png', dpi=150)
```

---

### 13.3 Radar Chart (Profil Risiko per Cluster)

**Nama File:** `visualisasi_radar_chart.png`

**Deskripsi:**  
Menampilkan **profil klinis/risiko setiap klaster** dalam bentuk radar chart (spider chart), berdasarkan nilai **pusat klaster (centroid)** untuk semua 7 fitur.

**Spesifikasi Plot:**
- 7 sumbu (spoke) = 7 fitur:
  1. Usia Ibu
  2. Usia Kehamilan
  3. Gravida
  4. Tekanan Darah
  5. Denyut Jantung Janin
  6. Nilai AFI
  7. Kejadian KPD
- Rentang nilai setiap sumbu: 0.0 – 1.0 (nilai ternormalisasi)
- 3 poligon berbeda warna untuk K1, K2, K3 dengan transparansi (alpha = 0.25)
- Garis tepi poligon tebal dan solid
- Titik pada setiap sudut
- Judul: `"Radar Chart – Profil Risiko per Klaster"`
- Legend: K1 Mild, K2 Moderate, K3 Severe

**Interpretasi:**
- Klaster Severe (K3) akan memiliki area radar lebih besar pada fitur Tekanan Darah dan DJJ, namun lebih kecil pada Nilai AFI
- Klaster Mild (K1) akan menunjukkan area seimbang dengan Nilai AFI relatif lebih tinggi

**Kode Referensi:**
```python
import matplotlib.pyplot as plt
import numpy as np

features = ['Usia Ibu', 'Usia Kehamilan', 'Gravida', 'Tekanan Darah',
            'DJJ', 'Nilai AFI', 'Kejadian KPD']
N = len(features)
angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
angles += angles[:1]  # tutup poligon

fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))
colors = ['#40DF00', '#FF9800', '#F44336']
labels = ['K1 – Mild', 'K2 – Moderate', 'K3 – Severe']

for k in range(3):
    vals = centroids[k].tolist()
    vals += vals[:1]
    ax.plot(angles, vals, color=colors[k], linewidth=2, label=labels[k])
    ax.fill(angles, vals, color=colors[k], alpha=0.25)

ax.set_thetagrids(np.degrees(angles[:-1]), features)
ax.set_ylim(0, 1)
ax.set_title('Radar Chart – Profil Risiko per Klaster', pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
plt.tight_layout()
plt.savefig('visualisasi_radar_chart.png', dpi=150)
```

---

### 13.4 Heatmap Cluster vs Variabel

**Nama File:** `visualisasi_heatmap.png`

**Deskripsi:**  
Menampilkan **nilai rata-rata setiap fitur per klaster** dalam bentuk heatmap berwarna, sehingga mudah mengidentifikasi fitur mana yang paling membedakan antar klaster.

**Spesifikasi Plot:**
- Baris = 3 klaster: K1 Mild, K2 Moderate, K3 Severe
- Kolom = 7 fitur (Usia Ibu, Usia Kehamilan, Gravida, Tekanan Darah, DJJ, Nilai AFI, KPD)
- Colormap: `RdYlGn_r` (Merah = nilai tinggi/berisiko, Hijau = nilai rendah/aman)
- Anotasi nilai numerik di setiap sel (2 desimal)
- Colorbar di sisi kanan
- Judul: `"Heatmap Nilai Rata-rata Fitur per Klaster"`

**Data yang Digunakan:**
- Rata-rata nilai **ternormalisasi** setiap fitur untuk anggota tiap klaster (bukan nilai pusat klaster FCM, melainkan rata-rata aktual anggota klaster)

**Kode Referensi:**
```python
import seaborn as sns

# Hitung rata-rata per klaster
cluster_means = []
for k in [1, 2, 3]:
    idx = [i for i in range(len(data)) if dominant_cluster[i] == k]
    cluster_means.append(data[idx].mean(axis=0))

heatmap_data = np.array(cluster_means)
row_labels = ['K1 – Mild', 'K2 – Moderate', 'K3 – Severe']
col_labels  = ['Usia Ibu', 'Usia Kehamilan', 'Gravida', 'TD', 'DJJ', 'AFI', 'KPD']

fig, ax = plt.subplots(figsize=(11, 4))
sns.heatmap(heatmap_data, annot=True, fmt='.2f', cmap='RdYlGn_r',
            xticklabels=col_labels, yticklabels=row_labels,
            linewidths=0.5, linecolor='white', ax=ax, vmin=0, vmax=1)
ax.set_title('Heatmap Nilai Rata-rata Fitur per Klaster')
plt.tight_layout()
plt.savefig('visualisasi_heatmap.png', dpi=150)
```

---

### 13.5 Boxplot per Cluster

**Nama File:** `visualisasi_boxplot.png`

**Deskripsi:**  
Menampilkan **distribusi nilai setiap fitur** dikelompokkan per klaster menggunakan boxplot, sehingga terlihat sebaran, median, outlier, dan overlap antar klaster untuk setiap variabel.

**Spesifikasi Plot:**
- Layout: **7 subplot** (satu per fitur), disusun dalam grid 2 baris × 4 kolom (subplot ke-8 kosong)
- Sumbu X setiap subplot: K1 Mild | K2 Moderate | K3 Severe
- Sumbu Y: Nilai fitur (ternormalisasi)
- Warna box sesuai klaster: Biru / Oranye / Merah
- Tampilkan outlier sebagai titik (+)
- Garis median tebal (linewidth = 2)
- Judul global: `"Boxplot Distribusi Fitur per Klaster – FCM Oligohydramnion"`

**Fitur yang Divisualisasikan (per subplot):**
1. Usia Ibu
2. Usia Kehamilan
3. Gravida
4. Tekanan Darah
5. Denyut Jantung Janin (DJJ)
6. Nilai AFI
7. Kejadian KPD

**Kode Referensi:**
```python
feature_names = ['Usia Ibu', 'Usia Kehamilan', 'Gravida',
                 'Tekanan Darah', 'DJJ', 'Nilai AFI', 'KPD']
colors = ['#40DF00', '#FF9800', '#F44336']
fig, axes = plt.subplots(2, 4, figsize=(16, 8))
axes = axes.flatten()

for j, fname in enumerate(feature_names):
    ax = axes[j]
    plot_data = []
    for k in [1, 2, 3]:
        idx = [i for i in range(len(data)) if dominant_cluster[i] == k]
        plot_data.append(data[idx, j])
    bp = ax.boxplot(plot_data, patch_artist=True, labels=['K1\nMild','K2\nModerate','K3\nSevere'])
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    for median in bp['medians']:
        median.set_linewidth(2)
        median.set_color('black')
    ax.set_title(fname, fontsize=10)
    ax.grid(axis='y', alpha=0.3)

axes[-1].set_visible(False)  # sembunyikan subplot ke-8
fig.suptitle('Boxplot Distribusi Fitur per Klaster – FCM Oligohydramnion', fontsize=13, y=1.01)
plt.tight_layout()
plt.savefig('visualisasi_boxplot.png', dpi=150, bbox_inches='tight')
```

---

### 13.6 Validasi Clustering (Partition Coefficient Plot)

**Nama File:** `visualisasi_validasi_pc.png`

**Deskripsi:**  
Menampilkan **kurva nilai Partition Coefficient (PC) per iterasi** sehingga dapat dilihat konvergensi dan kualitas klasterisasi seiring bertambahnya iterasi. Dilengkapi dengan **grafik distribusi anggota klaster** (pie chart / bar chart).

**Layout:** 2 subplot berdampingan

#### Subplot 1 – Kurva PC per Iterasi
- Sumbu X: Nomor iterasi (1 hingga iterasi konvergen)
- Sumbu Y: Nilai PC (0 – 1)
- Garis berwarna biru dengan marker titik
- Garis horizontal putus-putus merah pada nilai PC akhir
- Anotasi nilai PC akhir: `"PC Final = x.xxxxxx"`
- Area interpretasi berwarna:
  - Hijau muda (0.8–1.0): Sangat Baik
  - Kuning (0.6–0.8): Baik
  - Oranye (0.4–0.6): Cukup
  - Merah muda (0–0.4): Buruk
- Judul subplot: `"Konvergensi Partition Coefficient per Iterasi"`

#### Subplot 2 – Distribusi Anggota Klaster
- Pie chart 3 irisan dengan warna K1/K2/K3
- Label: `"K1 – Mild: n (xx.x%)"`, dst.
- Judul subplot: `"Distribusi Anggota Klaster"`

**Kode Referensi:**
```python
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Subplot 1: Kurva PC
ax1.fill_between([0, max_iter], 0.8, 1.0, color='#C8E6C9', alpha=0.5, label='Sangat Baik')
ax1.fill_between([0, max_iter], 0.6, 0.8, color='#FFF9C4', alpha=0.5, label='Baik')
ax1.fill_between([0, max_iter], 0.4, 0.6, color='#FFE0B2', alpha=0.5, label='Cukup')
ax1.fill_between([0, max_iter], 0.0, 0.4, color='#FFCDD2', alpha=0.5, label='Buruk')
ax1.plot(iterations, pc_values, 'b-o', linewidth=2, markersize=5)
ax1.axhline(y=pc_final, color='red', linestyle='--', alpha=0.7)
ax1.text(len(pc_values)*0.6, pc_final + 0.01, f'PC Final = {pc_final:.6f}', color='red')
ax1.set_xlabel('Iterasi')
ax1.set_ylabel('Nilai Partition Coefficient')
ax1.set_title('Konvergensi Partition Coefficient per Iterasi')
ax1.legend(loc='lower right', fontsize=8)
ax1.set_ylim(0, 1.05)

# Subplot 2: Pie chart distribusi
sizes  = [count_k1, count_k2, count_k3]
colors = ['#40DF00', '#FF9800', '#F44336']
labels = [f'K1 – Mild\n{count_k1} pasien', f'K2 – Moderate\n{count_k2} pasien', f'K3 – Severe\n{count_k3} pasien']
ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90,
        wedgeprops={'edgecolor': 'white', 'linewidth': 2})
ax2.set_title('Distribusi Anggota Klaster')

fig.suptitle('Validasi Klasterisasi FCM – Oligohydramnion', fontsize=14)
plt.tight_layout()
plt.savefig('visualisasi_validasi_pc.png', dpi=150)
```

---

### 13.7 Ternary Plot (Membership Degree Ternary)

**Nama File:** `visualisasi_ternary_plot.png`

**Library Tambahan:** `mpltern` (install: `pip install mpltern`)

**Deskripsi:**  
Menampilkan setiap pasien sebagai titik dalam **ruang segitiga terner** di mana ketiga sudut mewakili keanggotaan penuh ke K1 (Mild), K2 (Moderate), dan K3 (Severe). Titik yang mendekati sudut = anggota tegas. Titik di tengah = data boundary/ambiguous.

**Spesifikasi Plot:**
- Tiga sumbu:
  - Kiri bawah-kanan: μ1 (K1 – Mild)
  - Kanan bawah-kiri: μ2 (K2 – Moderate)
  - Atas: μ3 (K3 – Severe)
- Rentang setiap sumbu: 0.0 – 1.0
- Warna titik: sesuai klaster dominan (K1=Biru, K2=Oranye, K3=Merah)
- Ukuran titik: 60 (uniform) atau proporsional terhadap nilai μ tertinggi
- Marker: lingkaran (○) dengan edge hitam tipis
- Anotasi nomor RM di samping titik (ukuran font kecil = 7pt) jika data ≤ 30
- Garis panduan (grid) pada μ = 0.25, 0.50, 0.75 untuk setiap sumbu
- Judul: `"Ternary Plot – Distribusi Keanggotaan Fuzzy (μ1, μ2, μ3)"`
- Label sudut:
  - Sudut kiri bawah: `"K1 – Mild\n(μ1 = 1.0)"`
  - Sudut kanan bawah: `"K2 – Moderate\n(μ2 = 1.0)"`
  - Sudut atas: `"K3 – Severe\n(μ3 = 1.0)"`
- Tambahkan titik segitiga di tengah (μ = 1/3 untuk semua) sebagai referensi "titik ekuilibrium"

**Interpretasi:**
- Titik di dekat sudut K1 (Biru) = pasien Mild dengan keyakinan tinggi
- Titik di dekat sudut K3 (Merah) = pasien Severe dengan keyakinan tinggi
- Titik mendekati pusat segitiga = data dengan ambiguitas tinggi, perlu kajian klinis lebih mendalam

**Kode Referensi:**
```python
import mpltern

fig = plt.figure(figsize=(9, 8))
ax = fig.add_subplot(111, projection='ternary')

colors_map = {1: '#40DF00', 2: '#FF9800', 3: '#F44336'}
point_colors = [colors_map[dominant_cluster[i]] for i in range(len(data))]

# t = μ3 (K3 Severe), l = μ1 (K1 Mild), r = μ2 (K2 Moderate)
t = U[2]   # μ3
l = U[0]   # μ1
r = U[1]   # μ2

sc = ax.scatter(t, l, r, c=point_colors, s=80, edgecolors='black', linewidths=0.5, zorder=5)

# Titik referensi ekuilibrium
ax.scatter([1/3], [1/3], [1/3], c='gray', s=150, marker='D', zorder=6, label='Ekuilibrium')

# Anotasi nomor RM (jika data ≤ 30)
if len(data) <= 30:
    for i, rm in enumerate(nomor_rm):
        ax.annotate(str(rm), (t[i], l[i], r[i]), fontsize=7, ha='left')

ax.set_tlabel('K3 – Severe\n(μ3 = 1.0)')
ax.set_llabel('K1 – Mild\n(μ1 = 1.0)')
ax.set_rlabel('K2 – Moderate\n(μ2 = 1.0)')
ax.taxis.set_ticks([0, 0.25, 0.5, 0.75, 1.0])
ax.laxis.set_ticks([0, 0.25, 0.5, 0.75, 1.0])
ax.raxis.set_ticks([0, 0.25, 0.5, 0.75, 1.0])
ax.grid(True, linestyle='--', alpha=0.4)

# Legend manual
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='#40DF00', label='K1 – Mild'),
    Patch(facecolor='#FF9800', label='K2 – Moderate'),
    Patch(facecolor='#F44336', label='K3 – Severe'),
]
ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.3, 1.0))

ax.set_title('Ternary Plot – Distribusi Keanggotaan Fuzzy (μ1, μ2, μ3)', pad=15)
plt.tight_layout()
plt.savefig('visualisasi_ternary_plot.png', dpi=150, bbox_inches='tight')
```

---

### 13.8 Ringkasan File Output Visualisasi

| No  | Nama File                         | Tipe Plot                   | Library Utama              |
|-----|-----------------------------------|-----------------------------|----------------------------|
| 1   | `visualisasi_scatter_plot.png`    | Scatter Plot                | matplotlib                 |
| 2   | `visualisasi_membership_degree.png`| Stacked Horizontal Bar     | matplotlib                 |
| 3   | `visualisasi_radar_chart.png`     | Radar / Spider Chart        | matplotlib (polar)         |
| 4   | `visualisasi_heatmap.png`         | Heatmap                     | seaborn + matplotlib       |
| 5   | `visualisasi_boxplot.png`         | Boxplot Grid                | matplotlib                 |
| 6   | `visualisasi_validasi_pc.png`     | Line Chart + Pie Chart      | matplotlib                 |
| 7   | `visualisasi_ternary_plot.png`    | Ternary / Simplex Plot      | mpltern + matplotlib       |

### 13.9 Instalasi Library Visualisasi

```bash
pip install matplotlib seaborn mpltern numpy pandas
```

### 13.10 Parameter Visual Global (Konsistensi Warna & Style)

```python
# Gunakan di awal script untuk konsistensi semua plot
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams.update({
    'font.family'       : 'DejaVu Sans',
    'font.size'         : 10,
    'axes.titlesize'    : 12,
    'axes.titleweight'  : 'bold',
    'axes.labelsize'    : 10,
    'figure.dpi'        : 150,
    'savefig.dpi'       : 150,
    'savefig.bbox'      : 'tight',
    'axes.spines.top'   : False,
    'axes.spines.right' : False,
})

# Palet warna klaster (gunakan konsisten di semua plot)
CLUSTER_COLORS = {
    1: '#40DF00',   # Mild     – Biru
    2: '#FF9800',   # Moderate – Oranye
    3: '#F44336',   # Severe   – Merah
}
CLUSTER_LABELS = {
    1: 'K1 – Mild',
    2: 'K2 – Moderate',
    3: 'K3 – Severe',
}
```

---

*Dokumen ini dibuat sebagai panduan implementasi sistem analisis klasterisasi faktor risiko oligohydramnion menggunakan FCM di RSU Srikandi IBI Jember.*

*Versi: 1.1 | Metode: Fuzzy C-Means | Jumlah Klaster: 3 (Mild, Moderate, Severe)*
