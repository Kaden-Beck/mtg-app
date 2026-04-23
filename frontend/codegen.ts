import type { CodegenConfig } from "@graphql-codegen/cli"

const config: CodegenConfig = {
    schema: "http://localhost:8000/graphql",
    documents: ["src/**/*.graphql"], 
    generates : {
        "./src/lib/gql/": {
            preset: "client",
            presetConfig: {
                gqlTagName: "gql"
            }
        }
    }
}

export default config