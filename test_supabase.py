import os
from supabase import create_client, Client
from dotenv import load_dotenv
import sys

def test_connection():
    load_dotenv()
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    print(f"--- Diagnóstico de Conexão Supabase ---")
    print(f"URL configurada: {url}")
    print(f"Key configurada: {key[:10]}...{key[-10:] if key else 'None'}")
    
    if not url or not key:
        print("ERRO: URL ou KEY não encontradas no arquivo .env")
        return

    try:
        print("\nTentando inicializar o cliente...")
        supabase: Client = create_client(url, key)
        print("Cliente inicializado com sucesso.")
        
        print("\nTentando consultar a tabela 'costumer'...")
        # Tenta buscar apenas 1 registro para testar
        response = supabase.table('costumer').select("*").limit(1).execute()
        print("Consulta executada com sucesso!")
        print(f"Dados recebidos: {response.data}")
        
    except Exception as e:
        print(f"\n❌ ERRO DETECTADO:")
        print(f"Tipo do erro: {type(e).__name__}")
        print(f"Mensagem: {str(e)}")
        
        if "getaddrinfo failed" in str(e) or "Failed to establish a new connection" in str(e):
            print("\nSugestão: Parece um problema de DNS ou conectividade de rede com a URL fornecida.")
        elif "401" in str(e) or "Invalid API key" in str(e):
            print("\nSugestão: A chave de API (Service Role ou Anon Key) parece inválida.")
        elif "404" in str(e):
            print("\nSugestão: A tabela 'costumer' pode não existir ou a URL do projeto está incorreta.")

if __name__ == "__main__":
    test_connection()
