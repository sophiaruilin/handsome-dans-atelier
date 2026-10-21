import { usePrefs } from '../prefs/context'

export default function FavoriteButton({ productId, label = false }: { productId: string; label?: boolean }) {
  const { isFavorite, toggleFavorite } = usePrefs()
  const saved = isFavorite(productId)
  return (
    <button
      type="button"
      className={`fav ${saved ? 'saved' : ''} ${label ? 'with-label' : ''}`}
      onClick={() => toggleFavorite(productId)}
      aria-pressed={saved}
      aria-label={saved ? 'Remove from saved items' : 'Save this item'}
      title={saved ? 'Saved' : 'Save for later'}
    >
      <span aria-hidden="true">{saved ? '♥' : '♡'}</span>
      {label && <span>{saved ? 'Saved' : 'Save'}</span>}
    </button>
  )
}
