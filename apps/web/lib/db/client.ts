import postgres from "postgres";

const globalForSql = globalThis as unknown as {
  sql: postgres.Sql | undefined;
};

export const sql = globalForSql.sql ?? postgres(process.env.DATABASE_URL!, {
  max: 10, // Limit maximum connections per pool to be gentle
  idle_timeout: 20, // Close idle connections after 20 seconds
});

if (process.env.NODE_ENV !== "production") {
  globalForSql.sql = sql;
}
