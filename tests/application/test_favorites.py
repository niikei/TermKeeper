from termkeeper.application import TermKeeperService
from termkeeper.domain import SearchQuery


def test_favorites_filter_meanings_search_and_suggestions() -> None:
    service = TermKeeperService()
    service.set_config("user.name", "Curator")
    erp = service.create_meaning("Enterprise Resource Planning", terms=("ERP",))
    crm = service.create_meaning("Customer Relationship Management", terms=("CRM",))

    favorite = service.favorite_meaning(erp.meaning_id)

    assert favorite.is_favorite is True
    assert favorite.updated_by_id is not None
    assert [item.meaning_id for item in service.meanings(favorite_only=True)] == [
        erp.meaning_id,
    ]
    assert service.search(
        SearchQuery("ERP", favorite_only=True),
    ).hits[0].meaning.meaning_id == erp.meaning_id
    assert service.search(SearchQuery("CRMM", favorite_only=True)).suggestions == ()

    unfavorited = service.unfavorite_meaning(erp.meaning_id)
    assert unfavorited.is_favorite is False
    assert service.meanings(favorite_only=True) == []
    assert service.get_meaning(crm.meaning_id).is_favorite is False
