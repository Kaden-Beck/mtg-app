/* eslint-disable */
import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type Maybe<T> = T | null;
export type InputMaybe<T> = T | null | undefined;
export type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]?: Maybe<T[SubKey]> };
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]: Maybe<T[SubKey]> };
export type MakeEmpty<T extends { [key: string]: unknown }, K extends keyof T> = { [_ in K]?: never };
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: { input: string; output: string; }
  String: { input: string; output: string; }
  Boolean: { input: boolean; output: boolean; }
  Int: { input: number; output: number; }
  Float: { input: number; output: number; }
  /** Date with time (isoformat) */
  DateTime: { input: any; output: any; }
  /** The `JSON` scalar type represents JSON values as specified by [ECMA-404](https://ecma-international.org/wp-content/uploads/ECMA-404_2nd_edition_december_2017.pdf). */
  JSON: { input: any; output: any; }
};

export type CardType = {
  __typename?: 'CardType';
  cmc: Scalars['Int']['output'];
  collectorNumber: Scalars['String']['output'];
  colorIdentity: Array<Scalars['String']['output']>;
  id: Scalars['String']['output'];
  imageUris?: Maybe<Scalars['JSON']['output']>;
  legalities?: Maybe<Scalars['JSON']['output']>;
  manaCost?: Maybe<Scalars['String']['output']>;
  name: Scalars['String']['output'];
  oracleText?: Maybe<Scalars['String']['output']>;
  priceEur?: Maybe<Scalars['Int']['output']>;
  priceUsd?: Maybe<Scalars['Int']['output']>;
  priceUsdFoil?: Maybe<Scalars['Int']['output']>;
  rarity: Scalars['String']['output'];
  setCode: Scalars['String']['output'];
  setName: Scalars['String']['output'];
  typeLine: Scalars['String']['output'];
};

export enum CollectionFormat {
  Archidekt = 'archidekt',
  Manabox = 'manabox',
  Moxfield = 'moxfield'
}

export type CollectionItemType = {
  __typename?: 'CollectionItemType';
  acquiredAt: Scalars['DateTime']['output'];
  card?: Maybe<CardType>;
  condition: Scalars['String']['output'];
  foil: Scalars['Boolean']['output'];
  id: Scalars['String']['output'];
  language: Scalars['String']['output'];
  purchasePriceCents?: Maybe<Scalars['Int']['output']>;
  quantity: Scalars['Int']['output'];
  scryfallId: Scalars['String']['output'];
};

export type ConversionResultType = {
  __typename?: 'ConversionResultType';
  count: Scalars['Int']['output'];
  csv: Scalars['String']['output'];
};

export type DeckCardType = {
  __typename?: 'DeckCardType';
  board: Scalars['String']['output'];
  card?: Maybe<CardType>;
  categories: Array<Scalars['String']['output']>;
  deckId: Scalars['String']['output'];
  foil: Scalars['Boolean']['output'];
  id: Scalars['String']['output'];
  quantity: Scalars['Int']['output'];
  scryfallId: Scalars['String']['output'];
};

export type DeckType = {
  __typename?: 'DeckType';
  commanderId?: Maybe<Scalars['String']['output']>;
  createdAt: Scalars['DateTime']['output'];
  deckCards: Array<DeckCardType>;
  description?: Maybe<Scalars['String']['output']>;
  format: Scalars['String']['output'];
  id: Scalars['String']['output'];
  name: Scalars['String']['output'];
  updatedAt: Scalars['DateTime']['output'];
};

export type Mutation = {
  __typename?: 'Mutation';
  addCardToDeck: DeckCardType;
  addToCollection: CollectionItemType;
  convertCsv: ConversionResultType;
  createDeck: DeckType;
};


export type MutationAddCardToDeckArgs = {
  board?: Scalars['String']['input'];
  categories?: Array<Scalars['String']['input']>;
  deckId: Scalars['String']['input'];
  quantity?: Scalars['Int']['input'];
  scryfallId: Scalars['String']['input'];
};


export type MutationAddToCollectionArgs = {
  condition?: Scalars['String']['input'];
  foil?: Scalars['Boolean']['input'];
  language?: Scalars['String']['input'];
  purchasePriceCents?: InputMaybe<Scalars['Int']['input']>;
  quantity?: Scalars['Int']['input'];
  scryfallId: Scalars['String']['input'];
};


export type MutationConvertCsvArgs = {
  csv: Scalars['String']['input'];
  fromFormat: CollectionFormat;
  toFormat: CollectionFormat;
};


export type MutationCreateDeckArgs = {
  commanderId?: InputMaybe<Scalars['String']['input']>;
  format?: Scalars['String']['input'];
  name: Scalars['String']['input'];
};

export type Query = {
  __typename?: 'Query';
  cardById?: Maybe<CardType>;
  collection: Array<CollectionItemType>;
  deck?: Maybe<DeckType>;
  decks: Array<DeckType>;
  searchCards: Array<CardType>;
};


export type QueryCardByIdArgs = {
  id: Scalars['String']['input'];
};


export type QueryDeckArgs = {
  id: Scalars['String']['input'];
};


export type QuerySearchCardsArgs = {
  limit?: Scalars['Int']['input'];
  query: Scalars['String']['input'];
};

export type ConvertCsvMutationVariables = Exact<{
  csv: Scalars['String']['input'];
  fromFormat: CollectionFormat;
  toFormat: CollectionFormat;
}>;


export type ConvertCsvMutation = { __typename?: 'Mutation', convertCsv: { __typename?: 'ConversionResultType', csv: string, count: number } };

export type SearchCardsQueryVariables = Exact<{
  query: Scalars['String']['input'];
  limit?: InputMaybe<Scalars['Int']['input']>;
}>;


export type SearchCardsQuery = { __typename?: 'Query', searchCards: Array<{ __typename?: 'CardType', id: string, name: string, setCode: string, setName: string, manaCost?: string | null, cmc: number, typeLine: string, colorIdentity: Array<string>, rarity: string, priceUsd?: number | null, priceUsdFoil?: number | null, imageUris?: any | null }> };

export type CardByIdQueryVariables = Exact<{
  id: Scalars['String']['input'];
}>;


export type CardByIdQuery = { __typename?: 'Query', cardById?: { __typename?: 'CardType', id: string, name: string, oracleText?: string | null, legalities?: any | null, imageUris?: any | null } | null };


export const ConvertCsvDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"ConvertCsv"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"csv"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"fromFormat"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"CollectionFormat"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"toFormat"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"CollectionFormat"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"convertCsv"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"csv"},"value":{"kind":"Variable","name":{"kind":"Name","value":"csv"}}},{"kind":"Argument","name":{"kind":"Name","value":"fromFormat"},"value":{"kind":"Variable","name":{"kind":"Name","value":"fromFormat"}}},{"kind":"Argument","name":{"kind":"Name","value":"toFormat"},"value":{"kind":"Variable","name":{"kind":"Name","value":"toFormat"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"csv"}},{"kind":"Field","name":{"kind":"Name","value":"count"}}]}}]}}]} as unknown as DocumentNode<ConvertCsvMutation, ConvertCsvMutationVariables>;
export const SearchCardsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"SearchCards"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"query"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"limit"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"Int"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"searchCards"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"query"},"value":{"kind":"Variable","name":{"kind":"Name","value":"query"}}},{"kind":"Argument","name":{"kind":"Name","value":"limit"},"value":{"kind":"Variable","name":{"kind":"Name","value":"limit"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"setCode"}},{"kind":"Field","name":{"kind":"Name","value":"setName"}},{"kind":"Field","name":{"kind":"Name","value":"manaCost"}},{"kind":"Field","name":{"kind":"Name","value":"cmc"}},{"kind":"Field","name":{"kind":"Name","value":"typeLine"}},{"kind":"Field","name":{"kind":"Name","value":"colorIdentity"}},{"kind":"Field","name":{"kind":"Name","value":"rarity"}},{"kind":"Field","name":{"kind":"Name","value":"priceUsd"}},{"kind":"Field","name":{"kind":"Name","value":"priceUsdFoil"}},{"kind":"Field","name":{"kind":"Name","value":"imageUris"}}]}}]}}]} as unknown as DocumentNode<SearchCardsQuery, SearchCardsQueryVariables>;
export const CardByIdDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"CardById"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"cardById"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"oracleText"}},{"kind":"Field","name":{"kind":"Name","value":"legalities"}},{"kind":"Field","name":{"kind":"Name","value":"imageUris"}}]}}]}}]} as unknown as DocumentNode<CardByIdQuery, CardByIdQueryVariables>;