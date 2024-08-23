import asyncio
import logging
import json
import time
from web3 import Web3
from telegram import Bot

# Логотип
def display_logo():
    logo = """
    \033[32m
    ███╗   ██╗ ██████╗ ██████╗ ███████╗██████╗ ██╗   ██╗███╗   ██╗███╗   ██╗███████╗██████╗ 
    ████╗  ██║██╔═══██╗██╔══██╗██╔════╝██╔══██╗██║   ██║████╗  ██║████╗  ██║██╔════╝██╔══██╗
    ██╔██╗ ██║██║   ██║██║  ██║█████╗  ██████╔╝██║   ██║██╔██╗ ██║██╔██╗ ██║█████╗  ██████╔╝
    ██║╚██╗██║██║   ██║██║  ██║██╔══╝  ██╔══██╗██║   ██║██║╚██╗██║██║╚██╗██║██╔══╝  ██╔══██╗
    ██║ ╚████║╚██████╔╝██████╔╝███████╗██║  ██║╚██████╔╝██║ ╚████║██║ ╚████║███████╗██║  ██║
    ╚═╝  ╚═══╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
    \033[0m
    Подписаться на канал may.crypto{🦅}, чтобы быть в курсе самых актуальных нод - https://t.me/maycrypto
    """
    print(logo)

# Асинхронная функция для отправки сообщений в Telegram с эмодзи
async def send_telegram_message(message):
    await bot.send_message(chat_id=CHAT_ID, text=message)

# Запрашиваем у пользователя информацию для двух кошельков
TELEGRAM_TOKEN = input("Введите API токен Telegram Бота: ")
CHAT_ID = input("Введите свой Telegram ID: ")

# Данные для первого кошелька
private_key_1 = input("Введите приватный ключ для кошелька 1: ")
public_address_1 = input("Введите публичный адрес для кошелька 1: ")

# Данные для второго кошелька
private_key_2 = input("Введите приватный ключ для кошелька 2: ")
public_address_2 = input("Введите публичный адрес для кошелька 2: ")

bet_amount = float(input("Введите сумму ставки для каждого кошелька (в ETH): "))

# Подключаем Telegram бота
bot = Bot(token=TELEGRAM_TOKEN)

# Настройка Web3
w3 = Web3(Web3.HTTPProvider('https://arb1.arbitrum.io/rpc'))

if not w3.is_connected():
    asyncio.run(send_telegram_message("❌ Не удалось подключиться к сети Arbitrum"))
    exit()

# Загрузка ABI контракта
with open('ContractABI.json', 'r') as abi_file:
    abi_content = json.load(abi_file)
    if isinstance(abi_content, dict) and 'result' in abi_content:
        contract_abi = json.loads(abi_content['result'])
    else:
        contract_abi = abi_content

contract_address = Web3.to_checksum_address('0x1cdc19b13729f16c5284a0ace825f83fc9d799f4')
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Конвертация суммы в Wei
bet_amount_wei = w3.to_wei(bet_amount, 'ether')

# Инициализация nonce для каждого кошелька
nonce_1 = w3.eth.get_transaction_count(public_address_1, 'pending')
nonce_2 = w3.eth.get_transaction_count(public_address_2, 'pending')

# Получение текущей эпохи
def get_current_epoch():
    return contract.functions.currentEpoch().call()

# Функция для проверки, была ли сделана ставка на текущую эпоху
def has_bet(epoch, public_address):
    try:
        return contract.functions.ledger(epoch, public_address).call()[1] > 0
    except Exception as e:
        print(f"Ошибка проверки ставки для эпохи {epoch}: {e}")
        return False

# Функция для ставок на рост (bull) для кошелька 1
async def bet_bull(epoch):
    global nonce_1
    base_fee = w3.eth.get_block('latest')['baseFeePerGas']
    max_priority_fee = w3.to_wei('2', 'gwei')
    max_fee_per_gas = base_fee + max_priority_fee
    gas_limit = 160860
    
    txn = contract.functions.betBull(epoch).build_transaction({
        'chainId': 42161,
        'gas': gas_limit,
        'maxFeePerGas': max_fee_per_gas,
        'maxPriorityFeePerGas': max_priority_fee,
        'nonce': nonce_1,
        'value': bet_amount_wei
    })
    
    signed_txn = w3.eth.account.sign_transaction(txn, private_key_1)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    nonce_1 += 1
    
    await send_telegram_message(f"✅ Ставка на рост (кошелек 1) сделана. 🚀\nЭпоха: {epoch}\nХэш транзакции: {tx_hash.hex()}\nСумма: {bet_amount} ETH")

# Функция для ставок на падение (bear) для кошелька 2
async def bet_bear(epoch):
    global nonce_2
    base_fee = w3.eth.get_block('latest')['baseFeePerGas']
    max_priority_fee = w3.to_wei('2', 'gwei')
    max_fee_per_gas = base_fee + max_priority_fee
    gas_limit = 160860
    
    txn = contract.functions.betBear(epoch).build_transaction({
        'chainId': 42161,
        'gas': gas_limit,
        'maxFeePerGas': max_fee_per_gas,
        'maxPriorityFeePerGas': max_priority_fee,
        'nonce': nonce_2,
        'value': bet_amount_wei
    })
    
    signed_txn = w3.eth.account.sign_transaction(txn, private_key_2)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    nonce_2 += 1
    
    await send_telegram_message(f"✅ Ставка на падение (кошелек 2) сделана. 🐻\nЭпоха: {epoch}\nХэш транзакции: {tx_hash.hex()}\nСумма: {bet_amount} ETH")

# Основная функция для запуска всех задач с периодичностью 10 минут
async def main():
    # Показ логотипа при запуске
    display_logo()

    # Логируем успешный запуск скрипта
    await send_telegram_message("🤖 Скрипт ставок запущен успешно.\n🕒 Два кошелька будут делать противоположные ставки каждые 10 минут.")

    while True:
        # Получаем текущую эпоху
        current_epoch = get_current_epoch()

        # Проверяем, была ли ставка сделана в этой эпохе
        if not has_bet(current_epoch, public_address_1):
            await bet_bull(current_epoch)

        if not has_bet(current_epoch, public_address_2):
            await bet_bear(current_epoch)

        await send_telegram_message("💸 Ставки успешно сделаны с обоих кошельков.")

        # Оповещение за 2 минуты до следующей ставки
        await asyncio.sleep(480)  # 480 секунд = 8 минут
        await send_telegram_message("⏳ Через 2 минуты начнется следующая ставка...")
        
        # Ждем оставшиеся 2 минуты до следующей итерации
        await asyncio.sleep(120)  # 120 секунд = 2 минуты

# Запускаем основной цикл
asyncio.run(main())
