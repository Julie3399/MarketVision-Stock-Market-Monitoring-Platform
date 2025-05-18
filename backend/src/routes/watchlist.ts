import express from 'express';
import fs from 'fs/promises';
import path from 'path';

const router = express.Router();
const watchlistPath = path.join(__dirname, '../../data/watchlist.json');

// Read watchlist file
async function readWatchlist() {
  const data = await fs.readFile(watchlistPath, 'utf8');
  return JSON.parse(data);
}

// Write watchlist file
async function writeWatchlist(data: any) {
  await fs.writeFile(watchlistPath, JSON.stringify(data, null, 2), 'utf8');
}

// Add stock
router.post('/add', async (req, res) => {
  try {
    const { symbol, group = 'Default Group' } = req.body;
    const watchlist = await readWatchlist();

    if (!watchlist[group]) {
      watchlist[group] = {
        description: null,
        stocks: [],
        subGroups: {}
      };
    }

    if (!watchlist[group].stocks.includes(symbol)) {
      watchlist[group].stocks.push(symbol);
    }

    await writeWatchlist(watchlist);
    res.json({ success: true });
  } catch (error) {
    console.error('Failed to add stock:', error);
    res.status(500).json({ error: 'Failed to add stock' });
  }
});

// Delete stock
router.delete('/:group/:symbol', async (req: express.Request, res: express.Response) => {
  try {
    const { group, symbol } = req.params;
    const watchlist = await readWatchlist();

    // If deleting from Default Group, remove from all groups
    if (group === 'Default Group') {
      Object.keys(watchlist).forEach(groupName => {
        if (watchlist[groupName].stocks) {
          watchlist[groupName].stocks = watchlist[groupName].stocks.filter((s: string) => s !== symbol);
        }
      });
    } else {
      // Delete from specified group
      if (!watchlist[group]) {
        return res.status(404).json({ error: `Group ${group} does not exist` });
      }

      if (!watchlist[group].stocks.includes(symbol)) {
        return res.status(404).json({ error: `Stock ${symbol} is not in group ${group}` });
      }

      watchlist[group].stocks = watchlist[group].stocks.filter((s: string) => s !== symbol);
    }

    // If group is empty and not Default Group, delete the group
    Object.keys(watchlist).forEach(groupName => {
      if (groupName !== 'Default Group' && 
          watchlist[groupName].stocks.length === 0 && 
          (!watchlist[groupName].subGroups || Object.keys(watchlist[groupName].subGroups).length === 0)) {
        delete watchlist[groupName];
      }
    });

    await writeWatchlist(watchlist);
    res.json({ 
      success: true,
      message: `Removed ${symbol} from ${group}`,
      groups: watchlist
    });
  } catch (error) {
    console.error('Failed to delete stock:', error);
    res.status(500).json({ error: 'Failed to delete stock' });
  }
});

// Move stock
router.post('/move', async (req, res) => {
  try {
    const { symbol, fromGroup, toGroup } = req.body;
    const watchlist = await readWatchlist();

    // Remove from source group
    if (watchlist[fromGroup]) {
      watchlist[fromGroup].stocks = watchlist[fromGroup].stocks.filter((s: string) => s !== symbol);
    }

    // Add to target group
    if (!watchlist[toGroup]) {
      watchlist[toGroup] = {
        description: null,
        stocks: [],
        subGroups: {}
      };
    }
    
    if (!watchlist[toGroup].stocks.includes(symbol)) {
      watchlist[toGroup].stocks.push(symbol);
    }

    await writeWatchlist(watchlist);
    res.json({ success: true });
  } catch (error) {
    console.error('Failed to move stock:', error);
    res.status(500).json({ error: 'Failed to move stock' });
  }
});

export default router;
