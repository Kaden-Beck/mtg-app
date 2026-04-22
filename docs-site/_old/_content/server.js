import express from "express";
import mongoose from "mongoose";
import cors from "cors";
import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";

dotenv.config();

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, "content")));

// ── Schema ────────────────────────────────────────────────
const progressSchema = new mongoose.Schema({
    guideId: { type: String, required: true, unique: true },
    completed: { type: [String], default: [] },   // lesson IDs
    updatedAt: { type: Date, default: Date.now },
});

const Progress = mongoose.model("Progress", progressSchema);

// ── Routes ────────────────────────────────────────────────

// GET /api/progress/:guideId
app.get("/api/progress/:guideId", async (req, res) => {
    const doc = await Progress.findOne({ guideId: req.params.guideId });
    res.json({ completed: doc?.completed ?? [] });
});

// POST /api/progress/:guideId
// Body: { completed: ["01", "02", ...] }
app.post("/api/progress/:guideId", async (req, res) => {
    const { completed } = req.body;
    const doc = await Progress.findOneAndUpdate(
        { guideId: req.params.guideId },
        { completed, updatedAt: new Date() },
        { upsert: true, new: true }
    );
    res.json({ completed: doc.completed });
});

// ── Start ─────────────────────────────────────────────────
mongoose.connect(process.env.MONGO_URI).then(() => {
    console.log("MongoDB connected");
    app.listen(process.env.PORT, () => {
        console.log(`Server running on http://localhost:${process.env.PORT}`);
    });
}); 