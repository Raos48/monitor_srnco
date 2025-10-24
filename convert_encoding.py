import json

input_filename = 'backup_supa.json'
output_filename = 'backup_utf8.json'

print(f"Lendo o arquivo '{input_filename}' com encoding 'latin-1'...")

try:
    # Abre o arquivo original lendo como latin-1
    with open(input_filename, 'r', encoding='latin-1') as f_in:
        data = json.load(f_in)

    # Abre um novo arquivo para escrever como utf-8
    with open(output_filename, 'w', encoding='utf-8') as f_out:
        # Garante que caracteres não-ascii sejam escritos corretamente
        json.dump(data, f_out, indent=2, ensure_ascii=False)

    print(f"Sucesso! O arquivo foi convertido e salvo como '{output_filename}'.")
    print("Agora você pode rodar 'python manage.py loaddata backup_utf8.json'")

except Exception as e:
    print(f"\nOcorreu um erro durante a conversão: {e}")
    print("Verifique se o nome do arquivo de entrada está correto e se ele não está corrompido.")
