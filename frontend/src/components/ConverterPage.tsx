import { useMutation } from "@apollo/client/react";
import { ConvertCsvDocument } from "@/lib/gql/graphql";

export function ConverterPage() {
  const [convert, { data, loading }] = useMutation(ConvertCsvDocument);

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const csv = await file.text();
    await convert({ variables: { csv, fromFormat, toFormat } });
  };

  const handleDownload = () => {
    if (!data?.convertCsv.csv) return;
    const blob = new Blob([data.convertCsv.csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "converted.csv";
    a.click();
  };

  return (/* JSX with file input, format selects, download button */);
}