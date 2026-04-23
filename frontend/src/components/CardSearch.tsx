// import { useQuery } from "@apollo/client";
// import { SearchCardsDocument } from "@/graphql/graphql";

// function CardSearch({ query }: { query: string }) {
//   const { data, loading } = useQuery(SearchCardsDocument, {
//     variables: { query, limit: 20 },
//     skip: query.length < 2,
//   });

//   return <div>{data?.searchCards.map(c => c.name).join(", ")}</div>;
// }