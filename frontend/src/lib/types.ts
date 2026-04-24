import type { ScryfallColors, ScryfallImageUris, ScryfallLanguageCodeLike } from "@scryfall/api-types";

// Format-agnostic internal representation
export interface CanonicalCard {
  scryfallId: string;
  quantity: number;
  foil: boolean;
  condition: CardCondition;
  language: ScryfallLanguageCodeLike;
  purchasePrice?: number;
}

export type CardCondition =
  | "NM" | "LP" | "MP" | "HP" | "DMG";

// A card as it lives inside a deck (from GraphQL)
export interface DeckCardView {
  id: string;
  deckId: string;
  scryfallId: string;
  quantity: number;
  board: "mainboard" | "sideboard" | "maybeboard" | "commander";
  categories: string[];
  foil: boolean;
  card?: {
    id: string;
    name: string;
    manaCost?: string;
    cmc: number;
    typeLine: string;
    colorIdentity: ScryfallColors;
    priceUsd?: number;
    imageUris?: ScryfallImageUris;
  };
}

export type CollectionFormat = "manabox" | "moxfield" | "archidekt";