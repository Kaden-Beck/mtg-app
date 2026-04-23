import { useQuery } from "@apollo/client/react";
import { SearchCardsDocument } from "@/lib/gql/graphql";
import type { SearchCardsQuery, SearchCardsQueryVariables } from "@/lib/gql/graphql";

export default function CardSearch({ query }: { query: string }) {
  const { data, loading } = useQuery<SearchCardsQuery, SearchCardsQueryVariables>(SearchCardsDocument, {
    variables: { query, limit: 20 },
    skip: query.length < 2,
  });

  return <div>{data?.searchCards.map(c => c.name).join(", ")}</div>;
}
