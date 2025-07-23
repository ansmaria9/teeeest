import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import json
import hashlib

# Konfigurasi halaman
st.set_page_config(
    page_title="Tes Rekrutmen Online",
    page_icon="📝",
    layout="wide"
)

# Inisialisasi database
def init_database():
    conn = sqlite3.connect('recruitment_test.db')
    cursor = conn.cursor()
    
    # Tabel untuk peserta
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            position TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabel untuk jawaban
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participant_id INTEGER,
            question_id INTEGER,
            answer TEXT,
            is_correct BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (participant_id) REFERENCES participants (id)
        )
    ''')
    
    # Tabel untuk hasil tes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participant_id INTEGER,
            total_questions INTEGER,
            correct_answers INTEGER,
            score REAL,
            completion_time INTEGER,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (participant_id) REFERENCES participants (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Bank soal (bisa disesuaikan dengan kebutuhan)
QUESTIONS = [
    {
        "id": 1,
        "question": "Apa kepanjangan dari HTML?",
        "options": [
            "Hyper Text Markup Language",
            "High Tech Modern Language", 
            "Home Tool Markup Language",
            "Hyperlink Text Management Language"
        ],
        "correct": 0,
        "category": "Technical"
    },
    {
        "id": 2,
        "question": "Manakah yang bukan merupakan bahasa pemrograman?",
        "options": ["Python", "JavaScript", "HTML", "Java"],
        "correct": 2,
        "category": "Technical"
    },
    {
        "id": 3,
        "question": "Apa yang dimaksud dengan responsive design?",
        "options": [
            "Design yang cepat loading",
            "Design yang dapat beradaptasi dengan berbagai ukuran layar",
            "Design yang interaktif",
            "Design yang menggunakan banyak animasi"
        ],
        "correct": 1,
        "category": "Technical"
    },
    {
        "id": 4,
        "question": "Dalam tim, bagaimana Anda menangani konflik?",
        "options": [
            "Menghindari konflik",
            "Memaksakan pendapat sendiri",
            "Mendengarkan semua pihak dan mencari solusi bersama",
            "Menyerahkan pada atasan"
        ],
        "correct": 2,
        "category": "Soft Skills"
    },
    {
        "id": 5,
        "question": "Apa yang Anda lakukan ketika menghadapi deadline yang ketat?",
        "options": [
            "Panik dan stress",
            "Menunda pekerjaan",
            "Membuat prioritas dan mengatur waktu dengan baik",
            "Meminta perpanjangan waktu"
        ],
        "correct": 2,
        "category": "Soft Skills"
    }
]

# Fungsi untuk menyimpan data peserta
def save_participant(name, email, phone, position):
    conn = sqlite3.connect('recruitment_test.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO participants (name, email, phone, position)
            VALUES (?, ?, ?, ?)
        ''', (name, email, phone, position))
        conn.commit()
        participant_id = cursor.lastrowid
        conn.close()
        return participant_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

# Fungsi untuk menyimpan jawaban
def save_answer(participant_id, question_id, answer, is_correct):
    conn = sqlite3.connect('recruitment_test.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO answers (participant_id, question_id, answer, is_correct)
        VALUES (?, ?, ?, ?)
    ''', (participant_id, question_id, answer, is_correct))
    
    conn.commit()
    conn.close()

# Fungsi untuk menyimpan hasil tes
def save_test_result(participant_id, total_questions, correct_answers, score, completion_time):
    conn = sqlite3.connect('recruitment_test.db')
    cursor = conn.cursor()
    
    status = "LULUS" if score >= 70 else "TIDAK LULUS"
    
    cursor.execute('''
        INSERT INTO test_results (participant_id, total_questions, correct_answers, score, completion_time, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (participant_id, total_questions, correct_answers, score, completion_time, status))
    
    conn.commit()
    conn.close()

# Fungsi untuk mengambil data hasil tes
def get_test_results():
    conn = sqlite3.connect('recruitment_test.db')
    query = '''
        SELECT p.name, p.email, p.position, tr.score, tr.status, tr.created_at
        FROM test_results tr
        JOIN participants p ON tr.participant_id = p.id
        ORDER BY tr.created_at DESC
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Inisialisasi database
init_database()

# Sidebar untuk navigasi
st.sidebar.title("📝 Tes Rekrutmen Online")
page = st.sidebar.selectbox("Pilih Halaman", ["Tes Peserta", "Dashboard Admin"])

if page == "Tes Peserta":
    # Halaman untuk peserta tes
    if 'test_started' not in st.session_state:
        st.session_state.test_started = False
    
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    
    if 'answers' not in st.session_state:
        st.session_state.answers = {}
    
    if 'participant_id' not in st.session_state:
        st.session_state.participant_id = None
    
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None

    if not st.session_state.test_started:
        st.title("🎯 Selamat Datang di Tes Rekrutmen Online")
        st.markdown("---")
        
        st.subheader("📋 Informasi Tes")
        st.info("""
        - **Jumlah Soal**: 5 soal
        - **Waktu**: Tidak dibatasi
        - **Passing Score**: 70%
        - **Kategori**: Technical & Soft Skills
        
        Pastikan Anda mengisi data dengan benar sebelum memulai tes.
        """)
        
        st.subheader("👤 Data Peserta")
        with st.form("participant_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Nama Lengkap *", placeholder="Masukkan nama lengkap")
                email = st.text_input("Email *", placeholder="contoh@email.com")
            
            with col2:
                phone = st.text_input("No. Telepon", placeholder="081234567890")
                position = st.selectbox("Posisi yang Dilamar *", [
                    "Frontend Developer",
                    "Backend Developer", 
                    "Full Stack Developer",
                    "UI/UX Designer",
                    "Project Manager",
                    "Quality Assurance"
                ])
            
            submitted = st.form_submit_button("🚀 Mulai Tes", use_container_width=True)
            
            if submitted:
                if name and email and position:
                    participant_id = save_participant(name, email, phone, position)
                    if participant_id:
                        st.session_state.participant_id = participant_id
                        st.session_state.test_started = True
                        st.session_state.start_time = datetime.now()
                        st.rerun()
                    else:
                        st.error("Email sudah terdaftar! Gunakan email lain.")
                else:
                    st.error("Mohon lengkapi data yang wajib diisi (*)")
    
    else:
        # Halaman tes
        st.title("📝 Tes Rekrutmen Online")
        
        # Progress bar
        progress = st.session_state.current_question / len(QUESTIONS)
        st.progress(progress)
        st.write(f"Soal {st.session_state.current_question + 1} dari {len(QUESTIONS)}")
        
        if st.session_state.current_question < len(QUESTIONS):
            current_q = QUESTIONS[st.session_state.current_question]
            
            st.markdown("---")
            st.subheader(f"Soal {st.session_state.current_question + 1}")
            st.markdown(f"**Kategori**: {current_q['category']}")
            st.markdown(f"**{current_q['question']}**")
            
            # Pilihan jawaban
            answer = st.radio(
                "Pilih jawaban:",
                current_q['options'],
                key=f"q_{current_q['id']}"
            )
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col2:
                if st.button("➡️ Jawaban Selanjutnya", use_container_width=True):
                    # Simpan jawaban
                    selected_index = current_q['options'].index(answer)
                    is_correct = selected_index == current_q['correct']
                    
                    st.session_state.answers[current_q['id']] = {
                        'answer': answer,
                        'is_correct': is_correct
                    }
                    
                    # Simpan ke database
                    save_answer(st.session_state.participant_id, current_q['id'], answer, is_correct)
                    
                    st.session_state.current_question += 1
                    st.rerun()
        
        else:
            # Halaman hasil
            st.success("🎉 Tes telah selesai!")
            
            # Hitung skor
            total_questions = len(QUESTIONS)
            correct_answers = sum(1 for ans in st.session_state.answers.values() if ans['is_correct'])
            score = (correct_answers / total_questions) * 100
            
            # Hitung waktu penyelesaian
            completion_time = int((datetime.now() - st.session_state.start_time).total_seconds() / 60)
            
            # Simpan hasil
            save_test_result(st.session_state.participant_id, total_questions, correct_answers, score, completion_time)
            
            # Tampilkan hasil
            st.markdown("---")
            st.subheader("📊 Hasil Tes Anda")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Soal", total_questions)
            
            with col2:
                st.metric("Jawaban Benar", correct_answers)
            
            with col3:
                st.metric("Skor", f"{score:.1f}%")
            
            with col4:
                st.metric("Waktu", f"{completion_time} menit")
            
            if score >= 70:
                st.success(f"🎉 Selamat! Anda LULUS dengan skor {score:.1f}%")
            else:
                st.error(f"😔 Mohon maaf, Anda TIDAK LULUS. Skor Anda {score:.1f}% (minimal 70%)")
            
            if st.button("🔄 Tes Lagi", use_container_width=True):
                # Reset session state
                for key in ['test_started', 'current_question', 'answers', 'participant_id', 'start_time']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

elif page == "Dashboard Admin":
    # Halaman admin
    st.title("📊 Dashboard Admin")
    
    # Password sederhana untuk admin
    if 'admin_logged_in' not in st.session_state:
        st.session_state.admin_logged_in = False
    
    if not st.session_state.admin_logged_in:
        st.subheader("🔐 Login Admin")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if password == "admin123":  # Ganti dengan password yang lebih aman
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Password salah!")
    
    else:
        st.success("✅ Login berhasil!")
        
        # Logout button
        if st.button("Logout"):
            st.session_state.admin_logged_in = False
            st.rerun()
        
        st.markdown("---")
        
        # Statistik
        results_df = get_test_results()
        
        if not results_df.empty:
            st.subheader("📈 Statistik Keseluruhan")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Peserta", len(results_df))
            
            with col2:
                lulus = len(results_df[results_df['status'] == 'LULUS'])
                st.metric("Lulus", lulus)
            
            with col3:
                tidak_lulus = len(results_df[results_df['status'] == 'TIDAK LULUS'])
                st.metric("Tidak Lulus", tidak_lulus)
            
            with col4:
                avg_score = results_df['score'].mean()
                st.metric("Rata-rata Skor", f"{avg_score:.1f}%")
            
            st.markdown("---")
            
            # Tabel hasil
            st.subheader("📋 Hasil Tes Semua Peserta")
            
            # Filter
            col1, col2 = st.columns(2)
            with col1:
                status_filter = st.selectbox("Filter Status", ["Semua", "LULUS", "TIDAK LULUS"])
            with col2:
                position_filter = st.selectbox("Filter Posisi", ["Semua"] + list(results_df['position'].unique()))
            
            # Apply filters
            filtered_df = results_df.copy()
            if status_filter != "Semua":
                filtered_df = filtered_df[filtered_df['status'] == status_filter]
            if position_filter != "Semua":
                filtered_df = filtered_df[filtered_df['position'] == position_filter]
            
            # Display table
            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Download CSV
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Data CSV",
                data=csv,
                file_name=f"hasil_tes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
        else:
            st.info("Belum ada data peserta tes.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <small>© 2024 Sistem Tes Rekrutmen Online | Made with ❤️ using Streamlit</small>
</div>
""", unsafe_allow_html=True)
