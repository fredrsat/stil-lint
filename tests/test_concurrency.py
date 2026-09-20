import asyncio
from concurrent.futures import ThreadPoolExecutor

from stillint import jev
from stillint.bank import PhraseBank
from stillint.engine import Engine


def test_jev_cache_parallel_writes(tmp_path):
    db = tmp_path / "cache.db"

    def hammer(worker):
        cache = jev._Cache(db)
        for i in range(50):
            key = jev._Cache.key(f"tekst {worker} {i}", "spørsmål", "jev-1.13")
            cache.put(key, 0.5)
            assert cache.get(key) == 0.5

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(hammer, range(8)))  # reiser ved "database is locked"


def test_phrase_bank_parallel_writes(tmp_path):
    db = tmp_path / "bank.db"

    def hammer(worker):
        bank = PhraseBank(db)
        for i in range(30):
            bank.add(f"agent-{worker}", f"melding nummer {i} fra agent {worker} med litt innhold her")
        bank.close()

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(hammer, range(8)))

    bank = PhraseBank(db)
    assert bank.overlap("agent-0", "melding nummer 3 fra agent 0 med litt innhold her") > 0.9


def test_five_concurrent_checks(tmp_path):
    async def run():
        engine = Engine(bank_path=tmp_path / "bank.db")
        texts = [f"Bussen {500 + i} er {i + 2} minutter forsinket. Ny avgang 07:5{i} fra Solligata."
                 for i in range(5)]
        results = await asyncio.gather(*(
            engine.check_text(t, genre="varsel", channel="push", mode="fast", agent_id=f"a{i}")
            for i, t in enumerate(texts)
        ))
        assert all(r["verdict"] == "pass" for r in results)

    asyncio.run(run())
