import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, user='postgres', password='Lhd@800pm', dbname='postgres')
conn.autocommit = True
cur = conn.cursor()
cur.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'faers_pediatric' AND pid != pg_backend_pid()")
print(f'Terminated {len(cur.fetchall())} stale connections')
cur.close()
conn.close()
