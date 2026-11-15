"""Items: a small CRUD example that shows the pattern for your own resources.

Every endpoint needs a logged-in user, and every item is scoped to its
owner — fetching someone else's item by id is a 404, not a leak. Copy this
router when you add a real resource and delete it when you don't need it.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import get_current_user, get_store
from ..models import ItemCreate, ItemPublic
from ..store import NotFoundError, Store, UserRecord

router = APIRouter(prefix="/items", tags=["items"])


@router.post("", response_model=ItemPublic, status_code=status.HTTP_201_CREATED)
def create_item(
    data: ItemCreate,
    user: UserRecord = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> ItemPublic:
    """Create an item owned by the current user."""
    item = store.create_item(user.id, data.title)
    return ItemPublic(id=item.id, title=item.title, done=item.done)


@router.get("", response_model=list[ItemPublic])
def list_items(
    user: UserRecord = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> list[ItemPublic]:
    """List the current user's items, oldest first."""
    return [
        ItemPublic(id=item.id, title=item.title, done=item.done)
        for item in store.list_items(user.id)
    ]


@router.get("/{item_id}", response_model=ItemPublic)
def get_item(
    item_id: int,
    user: UserRecord = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> ItemPublic:
    """Fetch one of the current user's items by id."""
    try:
        item = store.get_item(item_id, user.id)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return ItemPublic(id=item.id, title=item.title, done=item.done)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    user: UserRecord = Depends(get_current_user),
    store: Store = Depends(get_store),
) -> None:
    """Delete one of the current user's items. Missing id is a 404."""
    try:
        store.delete_item(item_id, user.id)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
