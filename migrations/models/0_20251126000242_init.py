from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "deployments" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "name" VARCHAR(64) NOT NULL UNIQUE,
    "description" TEXT NOT NULL,
    "content" TEXT NOT NULL,
    "goal" TEXT,
    "model_id" VARCHAR(100) NOT NULL,
    "temperature" REAL NOT NULL DEFAULT 0.7,
    "max_tokens" INT NOT NULL DEFAULT 1000,
    "top_p" REAL NOT NULL DEFAULT 1,
    "frequency_penalty" REAL NOT NULL DEFAULT 0,
    "presence_penalty" REAL NOT NULL DEFAULT 0,
    "stop_sequences" JSON NOT NULL,
    "fallback_models" JSON NOT NULL,
    "tags" JSON NOT NULL,
    "category" VARCHAR(50) NOT NULL DEFAULT 'general',
    "author" VARCHAR(100) NOT NULL DEFAULT 'anonymous',
    "version" INT NOT NULL DEFAULT 1,
    "shadow_version" INT,
    "status" VARCHAR(8) NOT NULL DEFAULT 'active' /* ACTIVE: active\nINACTIVE: inactive\nARCHIVED: archived */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) /* Database model for prompt deployments. */;
CREATE INDEX IF NOT EXISTS "idx_deployments_name_a731c0" ON "deployments" ("name");
CREATE INDEX IF NOT EXISTS "idx_deployments_categor_34f88a" ON "deployments" ("category");
CREATE INDEX IF NOT EXISTS "idx_deployments_author_8863c4" ON "deployments" ("author");
CREATE INDEX IF NOT EXISTS "idx_deployments_status_ee5dd7" ON "deployments" ("status");
CREATE TABLE IF NOT EXISTS "execution_metrics" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "prompt_name" VARCHAR(64) NOT NULL,
    "version" INT NOT NULL,
    "model_used" VARCHAR(100) NOT NULL,
    "latency_ms" REAL NOT NULL,
    "input_tokens" INT NOT NULL,
    "output_tokens" INT NOT NULL,
    "total_tokens" INT NOT NULL,
    "estimated_cost_usd" REAL NOT NULL,
    "success" INT NOT NULL DEFAULT 1,
    "error_message" TEXT,
    "shadow_execution" INT NOT NULL DEFAULT 0,
    "trace_id" VARCHAR(32),
    "span_id" VARCHAR(16),
    "executed_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) /* Database model for execution metrics. */;
CREATE INDEX IF NOT EXISTS "idx_execution_m_prompt__c03e91" ON "execution_metrics" ("prompt_name");
CREATE INDEX IF NOT EXISTS "idx_execution_m_version_ad339b" ON "execution_metrics" ("version");
CREATE INDEX IF NOT EXISTS "idx_execution_m_model_u_ef15be" ON "execution_metrics" ("model_used");
CREATE INDEX IF NOT EXISTS "idx_execution_m_success_88af47" ON "execution_metrics" ("success");
CREATE INDEX IF NOT EXISTS "idx_execution_m_shadow__e62a9a" ON "execution_metrics" ("shadow_execution");
CREATE INDEX IF NOT EXISTS "idx_execution_m_trace_i_be439d" ON "execution_metrics" ("trace_id");
CREATE INDEX IF NOT EXISTS "idx_execution_m_execute_fe4707" ON "execution_metrics" ("executed_at");
CREATE INDEX IF NOT EXISTS "idx_execution_m_prompt__c88898" ON "execution_metrics" ("prompt_name", "executed_at");
CREATE INDEX IF NOT EXISTS "idx_execution_m_prompt__38b8e3" ON "execution_metrics" ("prompt_name", "version", "executed_at");
CREATE TABLE IF NOT EXISTS "traffic_routes" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "version" INT NOT NULL,
    "weight" INT NOT NULL,
    "model_override" VARCHAR(100),
    "deployment_id" CHAR(36) NOT NULL REFERENCES "deployments" ("id") ON DELETE CASCADE
) /* Database model for traffic routes. */;
CREATE TABLE IF NOT EXISTS "version_history" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "version" INT NOT NULL,
    "content_hash" VARCHAR(12) NOT NULL,
    "content" TEXT NOT NULL,
    "model_id" VARCHAR(100) NOT NULL,
    "temperature" REAL NOT NULL DEFAULT 0.7,
    "max_tokens" INT NOT NULL DEFAULT 1000,
    "top_p" REAL NOT NULL DEFAULT 1,
    "frequency_penalty" REAL NOT NULL DEFAULT 0,
    "presence_penalty" REAL NOT NULL DEFAULT 0,
    "stop_sequences" JSON NOT NULL,
    "fallback_models" JSON NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "created_by" VARCHAR(100) NOT NULL,
    "change_summary" TEXT,
    "deployment_id" CHAR(36) NOT NULL REFERENCES "deployments" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_version_his_deploym_2acee7" UNIQUE ("deployment_id", "version")
) /* Database model for version history. */;
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "eJztXH9P2zgY/ipR/tokDkH5MTSdTiq0u/UGdILCTeNQZBK3jUjsLHEG1cR3P9tJmsSxu6"
    "Q0JYX8s8FrP479+LX9/rD5pbvYgk6w3YOeg2cuROSMCfSP2i8dARfSH1RVtjQdeF5agQkI"
    "uHM4xppX5nJwFxAfmIQWjYETwC1WIzB92yM2RgzQAxQLAqjxxrQx9jXPx65HtExT26wtC5"
    "u0MRtNqsFCZP8IoUHwBJIp9Cn45paKbWTBRxgkv3r3xtiGjpUjwLZYA1xukJnHZVdXg94n"
    "XpN16c4wsRO6KK3tzcgUo3n1MLStbYZhZROIoA8ItDJ0oNBxYvISUdRjKiB+COddtVKBBc"
    "cgdBip+p/jEJmMS41/if2z/5deoJl9RaAwFpkYsSmy2YTRsT9Fo0rHzKU6+9TJ5+7Fu73D"
    "93yUOCATnxdyRvQnDqSTEkE5rymR/P8ClSdT4MupTOoLZNKO1kNjQs9ynOkueDQciCZkSn"
    "893F/A4XX3gtN4uM9pxHRtROvmPC7p8CLGZspetlsFEkfwkchJFGCr4TIRpGSm63o1bC5g"
    "b9T/NmKddoPgh5Nl7d1Z9xsn1J3FJafD87+T6hmWT06HxwK79POEbhZVmM1AWlblrE4wcK"
    "pQmtRfis94Pb9iOvkpZ8jOI/UmmsVsiprmt9LdnZ0SeymtpdxMeVmeSgJdj4069CVH0icH"
    "A4WGCjiB0TED1sXpzvaHWlS1N7w6Pu1rXy/6J4PLwfA8p5xRIRNRgU34KC/63VNRM+mEEX"
    "wPUVBkc4AUXOZBApU2qo1Iqg47z1DOCfvOH53d/Q/7R3uH+0e0Cu/LXPJhAdmD85Goidgz"
    "vGo6mCDWqX2728/grGbtG/uQDgSZM8ODCDhkVolOKXq9C7u51HrUvKfcwKWYlYFbYt348K"
    "WrOIg0D0p2zX8uh+dyVotIgdMrRId6Y9km2dIcOyC3dfGr39zW42SywS+2nkRDaSvvjbIG"
    "ROuJ9t+5A+a9kQYsylIugbacl+GcgEklopP6Lbtl2DXp6CfYl2zKan8gi6nLHygGqKI2nW"
    "dwm/cJDsq4BAdqj+Cg4BCAkHLhV2EyRayPR4Awmrk4DFbGZC3e1U/oB9I4ldIXyCDW6Ag0"
    "xwsIpsDCD0Z14orApfhbf/Bk5QwS6pVLDhu2gPsodDl9A9oFQM0miVGVoNe4mE1i/4TFla"
    "x3T0aD6/5HLarwHxqcJxIbJTK2+qioR2v55pSKLDE7Umb1H5VY+0fKlX8krnvTh4wjA0gC"
    "qT1aQmwXKo6lHFKYAyuGbic/NDRsRcdgDZEzi2d7UXhwcNa/HHXPvuZsgl531GclnbxDEU"
    "vfHQoTMW9E+3cw+qyxX7Xvw/O+aDrM642+66xP9ODCBqKbBrAyiplIE2JyExt61pITm0e2"
    "E/uiE8s7zxKd4/tMho4JmHfzAHzLyJVkDHkfjMe2afg4JDJ39TjGf/pyAR2gyDbFqeRR1N"
    "YFa2qeTG7erD8lqpxI09kvWDrGlHolUku8CjHXUWOfo7Y2kRqmSriDVcpVLHI7rigBCEx4"
    "r9m32ZdidvqP0AxZT88g7Z2pvKkgrbe16LoCTBCGyyHLX1qYt6TFLZW6syBH/f7Kwo0e3X"
    "Ywkkx51FC029K6hfKMlZir2t59qPvugzARZX1MAbY227TZVyEa6V6umsMVu0dRHjgM4BLZ"
    "4wS1kepXS4CDnuQ8Y+RKTKEFCZE8bJ2pkNouOqwiF2IjLyTV88cibH2Bo2YtbWpHL8VfAf"
    "dWCSSYAKc6fyLsrdIHA+q6cyffpEYRPS0kR8yCTVEObzfHJK4ZmiYMZC43xg4ESBEWTlEC"
    "k3cUVtOxPResmsfj4fA0F1A5HojX5a7Ojvv0GH+f51OirL6PfernBQH1Moukqu8mFoDtJU"
    "XpJcU4ITH3aasqrgS+Pg2We/oNU2EWloAVr4FmMTUpbq1W/F6nhBG/11Ha8KxI0FMPoIok"
    "ZiAbsvgFV+iwjCckRqMzjtChSGI2ilQgcnFiQICuJzOwah19LYmBKONTITNQZ6C3mB+QRH"
    "mlSQR1iLeYv1gqvhs3o0XNlAruSiDtY7QVHarPCMg2MobYdE/vAdqTqWSnV3KWAt4qZVEE"
    "FVPl8W2rUuy/iNxMo6OO+Gv6vFdqwql3xAJwlZvjizpzv9kLC2e7jExJ3Ab7dAmjL3BWuD"
    "8lz2FL3ok3lsZC/pqKffAwP3aL2kLHSwcFI8/spHt50u319aeXMZNktwUkhpLiUoHaVJJc"
    "aVjKVorb0eJ2ShlLMozEWroRdDY5mm9bM6o1o5pvE8Qvx40pCKZVLAIRt6HvecuEcnbVoZ"
    "zdQiinfbzfvjZvtLnavjafM9i+Nm9fm5cgrcEvd9vX5u1r800jtn1t3r42f/2ct8/PXlEy"
    "Ujaxd9WeuudQrTuS0jkFaAKNIHRdIHuztMBtLiA3JCexbue5TVC0CYq3nqDoQt82p7okJx"
    "GXbC1KQ4C0zu+yD2paV3zTQv0UQbZUJUGFeA6flxpoQjB7iYyA+qBWpwQ25JTuHByUOKVp"
    "LeUpzcuEv0jjSQI1C/4cjSeL0mwIgfWYOaq0gNr1UqcF1uZy1Xb+rszletFrgk//AwvTd/"
    "E="
)
